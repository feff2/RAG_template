import json
from typing import Optional
import redis  

from src.services.chat.chat_history import ChatHistory

DEFAULT_PREFIX = "chat:history:"
DEFAULT_TTL = None  

class RedisChatDB:
    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = DEFAULT_PREFIX, ttl: Optional[int] = DEFAULT_TTL):
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix
        self.ttl = ttl

    def _key(self, chat_id: str) -> str:
        return f"{self.prefix}{chat_id}"

    def get_chat(self, chat_id: str) -> ChatHistory:
        raw = self.client.get(self._key(chat_id))
        if raw:
            try:
                data = json.loads(raw)
                return ChatHistory(data)
            except Exception:
                return ChatHistory()
        return ChatHistory()

    def save_chat(self, chat_id: str, history: ChatHistory) -> None:
        payload = json.dumps(history.history, ensure_ascii=False)
        if self.ttl:
            self.client.set(self._key(chat_id), payload, ex=self.ttl)
        else:
            self.client.set(self._key(chat_id), payload)

    def clear_chat(self, chat_id: str) -> None:
        self.client.delete(self._key(chat_id))

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
