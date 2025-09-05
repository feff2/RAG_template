import httpx
from typing import List, Dict

class LLMOrchestrator:
    def __init__(self: "LLMOrchestrator", services: Dict[str, str], history_max_token: int):
        self.services = services
        self.history_max_token = history_max_token

    async def generate(self: "LLMOrchestrator", request_id: str, history: List[Dict[str, str]], query: str) -> str:
        encode_payload = {"request_id": request_id, "text": [query]}
        async with httpx.AsyncClient() as client:
            encode_resp = await client.post(self.services["bi_encoder"], json=encode_payload, timeout=30)
            encode_resp.raise_for_status()
            query_vec = encode_resp.json()["vectors"][0]

        search_payload = {
            "collection_name": "default",
            "query_dense": query_vec,
            "top_k": 10
        }
        async with httpx.AsyncClient() as client:
            search_resp = await client.post(self.services["db"], json=search_payload, timeout=30)
            search_resp.raise_for_status()
            candidates = search_resp.json()

        pairs = [(query, doc["text"]) for doc in candidates]
        rerank_payload = {"request_id": 1, "pairs": pairs}
        async with httpx.AsyncClient() as client:
            rerank_resp = await client.post(self.services["cross_encoder"], json=rerank_payload, timeout=30)
            rerank_resp.raise_for_status()
            scores = rerank_resp.json()["scores"]

        top_docs = [doc for _, doc in sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)][:3]

        context = self._build_prompt(history, query, top_docs)

        generate_payload = {"request_id": 1, "prompt": context}
        async with httpx.AsyncClient() as client:
            llm_resp = await client.post(self.services["llm"], json=generate_payload, timeout=60)
            llm_resp.raise_for_status()
            answer = llm_resp.json()["response"]

        return answer

    def _truncate_to_fit(self: "LLMOrchestrator", history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not history:
            return []

        def count_tokens(messages: List[Dict[str, str]]) -> int:
            return sum(len(m['content'].split()) for m in messages)

        system_messages = [m for m in history if m.get('role') == 'system']
        other_messages = [m for m in history if m.get('role') != 'system']

        truncated = []
        total_tokens = 0
        for msg in reversed(other_messages):
            msg_tokens = len(msg['content'].split())
            if total_tokens + msg_tokens > self.history_max_token:
                break
            truncated.insert(0, msg)
            total_tokens += msg_tokens

        return system_messages + truncated

    def _build_prompt(self, history: List[Dict[str, str]], query: str, docs: List[Dict]) -> str:
        truncated_history = self._truncate_to_fit(history)
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in truncated_history])
        context_text = "\n".join([f"- {doc['text']}" for doc in docs])

        prompt = f"""Контекст:
        {context_text}

        История диалога:
        {history_text}

        Новый вопрос: {query}
        Ответ:"""

        return prompt
