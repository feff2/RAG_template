from typing import List, Tuple

from haystack import Document

from src.services.chat.chat_history import ChatHistory
from src.services.db.redis_chat_db import RedisChatDB
from src.services.llm.llm import VllmClient
from src.services.llm.prompts import GET_MAIN_THEME, RAG_SYSTEM_PROMPT
from src.services.retrivers.pipeline import RetrievePipeline
from src.shared.logger import CustomLogger


class ChatEngine:
    def __init__(self) -> None:
        self.client = None
        self.chat_db = None
        self.retriever = None
        self.logger = CustomLogger("ChatEngine")

    def start(self) -> None:
        self.client = VllmClient()

        self.chat_db = RedisChatDB(
            redis_url="redis://localhost:6379/0", ttl=60 * 60 * 24
        )
        self.retriever = RetrievePipeline()

    def close(self) -> None:
        self.client = None
        self.chat_db = None
        self.retriever = None

    def user_query(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        history = self.chat_db.get_chat(user_id)

        if history.history == []:
            history.add_system_message(RAG_SYSTEM_PROMPT)

        history.add_user_message(message)
        self.chat_db.increment_question(message)

        links: List[str] = []
        retrieved_text = None

        retrieved_text, documents = self.retriever.run(message)
        history.add_user_message(retrieved_text)
        links = self.parse_links(documents)

        history.truncate_by_tokens()

        prompt_messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
        if retrieved_text:
            prompt_messages.append({"role": "system", "content": retrieved_text})
        prompt_messages.append({"role": "user", "content": message})

        self.logger.info("Prompt messages: ")
        answer = self.client.generate(prompt_messages)

        history.add_assistant_message(answer)
        self.chat_db.save_chat(user_id, history)

        return answer, links

    def parse_links(self, docs: List[Document]) -> List[str]:
        links = []
        for doc in docs:
            doc_meta = doc.meta
            if doc_meta.get("chunk_url") is None:
                links.append(doc_meta.get("common_url"))
            else:
                links.append(doc_meta.get("chunk_url"))
        return links

    def gen_main_theme(self, messages: ChatHistory) -> str:
        texts = [m["content"] for m in messages.history if m.get("role") != "system"]
        compact = "\n".join(texts[-6:])
        msgs = [
            {"role": "system", "content": GET_MAIN_THEME},
            {"role": "user", "content": compact},
        ]
        response = self.client.generate(msgs)
        return response.strip()
