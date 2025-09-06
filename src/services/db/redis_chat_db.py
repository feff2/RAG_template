import json
from typing import Optional

import redis

from src.services.chat.chat_history import ChatHistory

DEFAULT_HISTORY_PREFIX = "chat:history:"
DEFAULT_STATS_PREFIX = "chat:stats:"
DEFAULT_TTL = None


class RedisChatDB:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        history_prefix: str = DEFAULT_HISTORY_PREFIX,
        stats_prefix: str = DEFAULT_STATS_PREFIX,
        ttl: Optional[int] = DEFAULT_TTL,
    ) -> None:
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.history_prefix = history_prefix
        self.stats_prefix = stats_prefix
        self.ttl = ttl

    def _history_key(self, chat_id: str) -> str:
        return f"{self.history_prefix}{chat_id}"

    def _stats_key(self) -> str:
        return f"{self.stats_prefix}questions"

    def get_chat(self, chat_id: str) -> ChatHistory:
        raw = self.client.get(self._history_key(chat_id))
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
            self.client.set(self._history_key(chat_id), payload, ex=self.ttl)
        else:
            self.client.set(self._history_key(chat_id), payload)

    def clear_chat(self, chat_id: str) -> None:
        self.client.delete(self._history_key(chat_id))

    def increment_question(self, question: str) -> None:
        self.client.zincrby(self._stats_key(), 1, question)

    def get_top_questions(self, limit: int = 10) -> list[dict]:
        res = self.client.zrevrange(self._stats_key(), 0, limit - 1, withscores=True)
        return [{"question": q, "count": int(score)} for q, score in res]

    def clear_stats(self) -> None:
        self.client.delete(self._stats_key())

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
