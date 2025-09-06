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

    def user_query(self, user_id: str, message: str) -> str:
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

        self.chat_db.save_chat(user_id, history)

        self._persist_result(
            user_id=user_id,
            question=message,
            answer=answer,
            links=links,
            faithfulness=faithfulness_result,
        )

        return answer, links

    def _persist_result(
        self,
        user_id: str,
        question: str,
        answer: str,
        links: List[str],
        faithfulness: Dict[str, Any],
    ) -> None:
        record = {
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "faithfulness": faithfulness,
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
