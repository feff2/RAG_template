import time
import uuid
import hashlib
from typing import List, Tuple, Optional

from haystack import Document

from src.services.chat.chat_history import ChatHistory
from src.services.db.qdrant_chat_db import QdrantChatDB
from src.services.db.redis_chat_db import RedisChatDB
from src.services.llm.llm import VllmClient
from src.services.llm.prompts import GET_MAIN_THEME, RAG_SYSTEM_PROMPT
from src.services.retrivers.pipeline import RetrievePipeline
from src.shared.logger import CustomLogger


class ChatEngine:
    def __init__(self) -> None:
        self.client = None
        self.redis_chat_db = None
        self.qdrant_chat_db = None
        self.retriever = None
        self.logger = CustomLogger("ChatEngine")

    def start(self) -> None:
        self.client = VllmClient()

        self.redis_chat_db = RedisChatDB(
            redis_url="redis://localhost:6379/0", ttl=60 * 60 * 24
        )
        self.qdrant_chat_db = QdrantChatDB(
            url="http://localhost:6333",
            collection="chat_messages",
            vector_size=1536,
            recreate=False,
        )
        self.retriever = RetrievePipeline()

    def close(self) -> None:
        self.client = None
        try:
            if self.redis_chat_db:
                self.redis_chat_db.close()
        except Exception:
            pass
        try:
            if self.qdrant_chat_db:
                self.qdrant_chat_db.close()
        except Exception:
            pass
        self.redis_chat_db = None
        self.qdrant_chat_db = None
        self.retriever = None

    def _stable_point_id(self, chat_id: str, ts: float, text: str, idx: int) -> str:
        base = f"{chat_id}:{int(ts * 1000)}:{idx}:{text}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, base))

    def _sync_chat_to_qdrant(self, chat_id: str) -> None:
        if self.redis_chat_db is None or self.qdrant_chat_db is None:
            self.logger.warn("Redis or Qdrant DB not initialized; skipping sync")
            return

        try:
            history: ChatHistory = self.redis_chat_db.get_chat(chat_id)
            items = history.history or []
            q_items = []
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                text_field = self._find_text_field_in_msg(item)
                if not text_field:
                    continue
                text_val = item.get(text_field, "")
                if not text_val or not text_val.strip():
                    continue
                normalized = item.get("normalized") 
             
                ts = item.get("timestamp")
                if ts is None:
                    ts = item.get("created_at") or item.get("time") or time.time()
                try:
                    ts = float(ts)
                except Exception:
                    ts = time.time()

                role = item.get("role", "user")
                meta = {k: v for k, v in item.items() if k not in (text_field, "normalized", "role", "timestamp", "created_at", "time")}

                point_id = self._stable_point_id(chat_id, ts, text_val, idx)

                q_items.append(
                    {
                        "chat_id": chat_id,
                        "text": text_val,
                        "role": role,
                        "point_id": point_id,
                        "normalized": normalized,
                        "timestamp": ts,
                        "meta": meta,
                    }
                )

            if q_items:
                self.qdrant_chat_db.upsert_messages(q_items)
                self.logger.info(f"Synced {len(q_items)} messages from chat {chat_id} to Qdrant")

        except Exception as e:
            self.logger.exception(f"Failed to sync chat {chat_id} to Qdrant: {e}")

    def user_query(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        if self.redis_chat_db is None or self.client is None or self.retriever is None:
            raise RuntimeError("ChatEngine not started. Call start() first.")

        history = self.redis_chat_db.get_chat(user_id)

        if history.history == []:
            history.add_system_message(RAG_SYSTEM_PROMPT)

        history.add_user_message(message)

        self.redis_chat_db.increment_question(message)

        retrieved_text: Optional[str] = None
        links: List[str] = []

        retrieved_text, documents = self.retriever.run(message)
        if retrieved_text:
            history.add_system_message(retrieved_text)
        
        links = self.parse_links(documents or [])

        prompt_messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
        if retrieved_text:
            prompt_messages.append({"role": "system", "content": retrieved_text})
        prompt_messages.append({"role": "user", "content": message})

        self.logger.info(f"Prompt messages: {prompt_messages}")
        answer = self.client.generate(prompt_messages)

        history.add_assistant_message(answer)

        try:
            self.redis_chat_db.save_chat(user_id, history)
        except Exception as e:
            self.logger.exception(f"Failed to save chat to Redis for user {user_id}: {e}")

        try:
            self._sync_chat_to_qdrant(user_id)
        except Exception:
            self.logger.exception(f"Failed to save chat to Qdrant for user {user_id}: {e}")

        return answer, links

    def parse_links(self, docs: List[Document]) -> List[str]:
        links: List[str] = []
        for doc in docs:
            doc_meta = doc.meta or {}
            if doc_meta.get("chunk_url") is None:
                links.append(doc_meta.get("common_url"))
            else:
                links.append(doc_meta.get("chunk_url"))
        return [l for l in links if l]

    def gen_main_theme(self, messages: ChatHistory) -> str:
        texts = [m.get("content") or m.get("text") for m in messages.history if (isinstance(m, dict) and m.get("role") != "system")]
        compact = "\n".join([t for t in texts if t][-6:])
        msgs = [
            {"role": "system", "content": GET_MAIN_THEME},
            {"role": "user", "content": compact},
        ]
        response = self.client.generate(msgs)
        return response.strip()


    @staticmethod
    def _find_text_field_in_msg(message: dict[str, any]) -> Optional[str]:
        for key in ("text", "message", "user_message", "content", "msg"):
            v = message.get(key)
            if isinstance(v, str) and v.strip():
                return key
        return None