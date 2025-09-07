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


import copy
from typing import List, Tuple

from haystack import Document

from src.services.chat.chat_history import ChatHistory
from src.services.db.redis_chat_db import RedisChatDB
from src.services.llm.llm import VllmClient
from src.services.llm.prompts import (
    GET_MAIN_THEME,
    RAG_NEED_TO_RETRIEVE,
    RAG_SYSTEM_PROMPT,
)
from src.services.retrivers.pipeline import RetrievePipeline
from src.shared.logger import CustomLogger

logger = CustomLogger("ChatEngine")


class ChatEngine:
    def __init__(self) -> None:
        self.client = None
        self.chat_db = None
        self.retriever = None

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

        if self.need_retrieve(message):
            retrieved_text, documents = self.retriever.run(message)
            history.add_user_message(retrieved_text)
            links = self.parse_links(documents)

        history.truncate_by_tokens()

        prompt_messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
        if retrieved_text:
            prompt_messages.append({"role": "system", "content": retrieved_text})
        prompt_messages.append({"role": "user", "content": message})

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

    def need_retrieve(self, message: str) -> bool:
        msgs = [
            {"role": "system", "content": RAG_NEED_TO_RETRIEVE},
            {"role": "user", "content": message},
        ]
        response = self.client.generate(msgs)
        return "да" in response.lower()

    def gen_main_theme(self, messages: ChatHistory) -> str:
        texts = [m["content"] for m in messages.history if m.get("role") != "system"]
        compact = "\n".join(texts[-6:]) 
        msgs = [
            {"role": "system", "content": GET_MAIN_THEME},
            {"role": "user", "content": compact},
        ]
        response = self.client.generate(msgs)
        return response.strip()
