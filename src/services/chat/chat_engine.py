import copy
import json
import os
import time
from typing import List, Dict, Any, Union

from haystack import Document
from haystack.components.evaluators import FaithfulnessEvaluator
from haystack.dataclasses import ChatMessage

from src.services.chat.chat_history import ChatHistory
from src.services.db.redis_chat_db import RedisChatDB
from src.services.llm.llm import VllmClient
from src.services.llm.prompts import RAG_NEED_TO_RETRIEVE, RAG_SYSTEM_PROMPT
from src.services.retrivers.pipeline import RetrievePipeline


class VllmChatGeneratorAdapter:
    def __init__(self, vllm_client: VllmClient, max_tokens: int = 512, temperature: float = 0.0):
        self.client = vllm_client
        self.max_tokens = max_tokens
        self.temperature = temperature

    def _gen_one(self, text: str) -> ChatMessage:
        history = [{"role": "user", "content": text}]
        reply_text = self.client.generate(history)
        return ChatMessage.from_assistant(reply_text)

    def run(self, **kwargs) -> Dict[str, Any]:
        if "messages" in kwargs and kwargs["messages"] is not None:
            messages: List[ChatMessage] = kwargs["messages"]
            history = [{"role": m.role, "content": m.text} for m in messages]
            reply_text = self.client.generate(history)
            return {"replies": [ChatMessage.from_assistant(reply_text)]}

        prompts: Union[str, List[str], None] = kwargs.get("prompt")
        if prompts is None:
            prompts = kwargs.get("prompts")

        if prompts is None:
            raise ValueError("VllmChatGeneratorAdapter.run: expected 'messages' or 'prompt(s)'")

        if isinstance(prompts, str):
            prompts_list = [prompts]
        elif isinstance(prompts, list):
            prompts_list = [str(p) for p in prompts]
        else:
            prompts_list = [str(prompts)]

        replies: List[ChatMessage] = []
        for p in prompts_list:
            try:
                replies.append(self._gen_one(p))
            except Exception as e:
                replies.append(ChatMessage.from_assistant(f"[adapter-error] {e}"))

        return {"replies": replies}


class ChatEngine:
    def __init__(self) -> None:
        self.client = None
        self.chat_db = None
        self.retriever = None
        self.faithfulness_evaluator = None
        self.results_path = os.getenv("RESULTS_JSONL_PATH", "results.json")

    def start(self) -> None:
        self.client = VllmClient()
        self.chat_db = RedisChatDB(
            redis_url="redis://localhost:6379/0", ttl=60 * 60 * 24
        )
        self.retriever = RetrievePipeline()

        vllm_adapter = VllmChatGeneratorAdapter(self.client)
        self.faithfulness_evaluator = FaithfulnessEvaluator(chat_generator=vllm_adapter)

    def close(self) -> None:
        self.client = None
        self.chat_db = None
        self.retriever = None
        self.faithfulness_evaluator = None

    def user_query(self, user_id: str, message: str, target: Union[str, None] = None) -> str:
        history = self.chat_db.get_chat(user_id)

        if history.history == []:
            history.add_system_message(RAG_SYSTEM_PROMPT)

        history.add_user_message(message)

        self.chat_db.increment_question(message)
        links: List[str] = []
        documents: List[Document] = []

        copy_history = copy.deepcopy(history)
        if self.need_retrieve(copy_history):
            retrieved, documents = self.retriever.run(message)
            history.add_user_message(retrieved)
            links = self.parse_links(documents)

        history.truncate_by_tokens()

        answer = self.client.generate(history.history)
        history.add_assistant_message(answer)

        faithfulness_result: Dict[str, Any] = {}
        if self.faithfulness_evaluator is not None and documents:
            try:
                questions = [message]
                contexts = [[(doc.content or "") for doc in documents]]
                predicted_answers = [answer]
                result = self.faithfulness_evaluator.run(
                    questions=questions,
                    contexts=contexts,
                    predicted_answers=predicted_answers,
                )
                faithfulness_result = result
                print("FAITHFULNESS METRIC:", result)
            except Exception as e:
                faithfulness_result = {"error": str(e)}
                print("FAITHFULNESS ERROR:", e)

        correctness_result: Dict[str, Any] = {}
        correctness_score: Union[float, None] = None
        if target:
            try:
                correctness_result = self._llm_correctness_against_target(
                    question=message, answer=answer, target=target
                )
                if "overall_score" in correctness_result:
                    correctness_score = float(correctness_result["overall_score"])
                print("CORRECTNESS (TARGET) METRIC:", correctness_result)
            except Exception as e:
                correctness_result = {"error": str(e)}
                print("CORRECTNESS (TARGET) ERROR:", e)

        self.chat_db.save_chat(user_id, history)

        self._persist_result(
            user_id=user_id,
            question=message,
            answer=answer,
            links=links,
            target=target,
            faithfulness=faithfulness_result,
            correctness=correctness_result,
            correctness_score=correctness_score,
        )

        return answer, links

    def _llm_correctness_against_target(self, question: str, answer: str, target: str) -> Dict[str, Any]:
        sys_prompt = (
            "Вы — строгий и точный оценщик, сравнивающий ответ модели с эталонным (reference/ground-truth) ответом.\n"
            "Шаги:\n"
            "1) Выделите короткие атомарные факты (claims) из ЭТАЛОННОГО ответа (REFERENCE).\n"
            "2) Для каждого факта оцените, семантически ли ОТВЕТ МОДЕЛИ его подтверждает (1), "
            "подтверждает частично / присутствует неопределённость (0.5), или не подтверждает / противоречит (0).\n"
            "3) Выделите все явные противоречия из ОТВЕТА МОДЕЛИ относительно ЭТАЛОНА и перечислите их.\n"
            "Верните СТРОГИЙ JSON со следующими ключами: target_claims, entailment_scores, explanations, contradictions, overall_score.\n"
            "Правила:\n"
            "- target_claims: массив лаконичных фактов из ЭТАЛОННОГО ответа.\n"
            "- entailment_scores: массив той же длины, значения только из {1, 0.5, 0}.\n"
            "- explanations: короткое обоснование для каждой оценки.\n"
            "- contradictions: массив утверждений из ОТВЕТА МОДЕЛИ, которые противоречат ЭТАЛОНУ (может быть пустым).\n"
            "- overall_score: среднее значение по entailment_scores в диапазоне [0, 1].\n"
            "Никакого дополнительного текста вне JSON."
        )

        user_prompt = (
            f"ВОПРОС:\n{question}\n\n"
            f"ЭТАЛОННЫЙ ОТВЕТ (REFERENCE):\n{target}\n\n"
            f"ОТВЕТ МОДЕЛИ:\n{answer}\n\n"
            "Верни только JSON."
        )

        history = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = self.client.generate(history)

        data = self._parse_strict_json(raw)
        if "error" in data:
            return data

        tgt = data.get("target_claims", [])
        scores = data.get("entailment_scores", [])
        expls = data.get("explanations", [])
        contr = data.get("contradictions", [])

        n = min(len(tgt), len(scores), len(expls)) if expls else min(len(tgt), len(scores))
        tgt = tgt[:n]
        scores = [float(x) for x in scores[:n]]
        expls = expls[:n] if expls else [""] * n

        overall = (sum(scores) / n) if n else 0.0

        return {
            "target_claims": tgt,
            "entailment_scores": scores,
            "explanations": expls,
            "contradictions": contr or [],
            "overall_score": overall,
        }


    def _parse_strict_json(self, raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except Exception:
            json_match = self._extract_json_object(raw)
            if json_match:
                try:
                    return json.loads(json_match)
                except Exception:
                    pass
        return {"error": "non_json_output", "raw": raw}

    @staticmethod
    def _extract_json_object(text: str) -> Union[str, None]:
        candidates = []
        for open_ch, close_ch in [("{", "}"), ("[", "]")]:
            stack = []
            start_idx = None
            for i, ch in enumerate(text):
                if ch == open_ch:
                    if not stack:
                        start_idx = i
                    stack.append(ch)
                elif ch == close_ch and stack:
                    stack.pop()
                    if not stack and start_idx is not None:
                        candidates.append(text[start_idx: i + 1])
        candidates.sort(key=len, reverse=True)
        for c in candidates:
            try:
                json.loads(c)
                return c
            except Exception:
                continue
        return None

    def _persist_result(
        self,
        user_id: str,
        question: str,
        answer: str,
        links: List[str],
        target: Union[str, None],
        faithfulness: Dict[str, Any],
        correctness: Dict[str, Any],
        correctness_score: Union[float, None],
    ) -> None:
        record = {
            "ts": time.time(),
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "links": links,
            "target": target,
            "faithfulness": faithfulness,
            "correctness": correctness,
            "correctness_score": correctness_score,
            "correctness_mode": "target" if target else "skipped",
        }

        try:
            if os.path.exists(self.results_path):
                with open(self.results_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []

            data.append(record)

            d = os.path.dirname(self.results_path)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(self.results_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print("ERROR while persisting result:", e)

    def parse_links(self, docs: List[Document]) -> List[str]:
        links = []
        for doc in docs:
            doc_meta = doc.meta
            if doc_meta["chunk_url"] is None:
                links.append(doc_meta["common_url"])
            else:
                links.append(doc_meta["chunk_url"])
        return links

    def need_retrieve(self, messages: ChatHistory) -> bool:
        messages.add_system_message(RAG_NEED_TO_RETRIEVE)
        response = self.client.generate(messages.history)
        return "да" in response.lower()
