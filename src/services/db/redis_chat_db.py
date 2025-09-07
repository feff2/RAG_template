import json
import re
from typing import Any, Dict, List, Optional

import pymorphy3
import redis

from src.services.chat.chat_history import ChatHistory

DEFAULT_HISTORY_PREFIX = "chat:history:"
DEFAULT_STATS_PREFIX = "chat:stats:"
DEFAULT_STATS_EXAMPLES_PREFIX = "chat:stats:examples:"
DEFAULT_THEME_PREFIX = "chat:theme:"
DEFAULT_TTL = None
THEME_STATS_KEY = "chat:stats:themes"
THEME_EXAMPLES_KEY = "chat:stats:themes:examples"

_morph = pymorphy3.MorphAnalyzer()


def normalize_text(text: str) -> str:
    if not text:
        return ""
    tokens = re.findall(r"\w+", text.lower())
    lemmas = []
    for t in tokens:
        try:
            lemmas.append(_morph.parse(t)[0].normal_form)
        except Exception:
            lemmas.append(t)
    return " ".join(lemmas)


def _find_text_field(message: Dict[str, Any]) -> Optional[str]:
    for key in ("text", "message", "user_message", "content", "msg"):
        v = message.get(key)
        if isinstance(v, str) and v.strip():
            return key
    return None


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
        self.stats_examples_prefix = DEFAULT_STATS_EXAMPLES_PREFIX
        self.theme_prefix = DEFAULT_THEME_PREFIX
        self.ttl = ttl

    def _history_key(self, chat_id: str) -> str:
        return f"{self.history_prefix}{chat_id}"

    def _stats_key(self) -> str:
        return f"{self.stats_prefix}questions"

    def _examples_key(self, normalized: str) -> str:
        return f"{self.stats_examples_prefix}{normalized}"

    def _theme_key(self, chat_id: str) -> str:
        return f"{self.theme_prefix}{chat_id}"

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
        try:
            enriched: List[Dict[str, Any]] = []
            for item in history.history:
                if isinstance(item, dict):
                    msg = item.copy()
                    text_field = _find_text_field(msg)
                    if text_field:
                        text_val = msg.get(text_field, "")
                        norm = normalize_text(text_val)
                        msg["normalized"] = norm
                    enriched.append(msg)
                else:
                    enriched.append(item)
            payload = json.dumps(enriched, ensure_ascii=False)
        except Exception:
            payload = json.dumps(history.history, ensure_ascii=False)

        if self.ttl:
            self.client.set(self._history_key(chat_id), payload, ex=self.ttl)
        else:
            self.client.set(self._history_key(chat_id), payload)

    def clear_chat(self, chat_id: str) -> None:
        self.client.delete(self._history_key(chat_id))

    def increment_question(self, question: str) -> None:
        norm = normalize_text(question)
        self.client.zincrby(self._stats_key(), 1, norm)
        try:
            self.client.sadd(self._examples_key(norm), question)
        except Exception:
            pass

    def get_top_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        res = self.client.zrevrange(self._stats_key(), 0, limit - 1, withscores=True)
        out: List[Dict[str, Any]] = []
        for q, score in res:
            examples = []
            try:
                members = list(self.client.srandmember(self._examples_key(q), 5) or [])
                examples = [m for m in members if isinstance(m, str)]
            except Exception:
                examples = []
            out.append({"normalized": q, "count": int(score), "examples": examples})
        return out

    def clear_stats(self) -> None:
        self.client.delete(self._stats_key())

    def get_theme(self, chat_id: str) -> Optional[str]:
        return self.client.get(self._theme_key(chat_id))

    def get_normalized_theme(self, chat_id: str) -> Optional[str]:
        try:
            return self.client.get(f"{self._theme_key(chat_id)}:normalized")
        except Exception:
            return None

    def save_theme(self, chat_id: str, theme: str) -> None:
        norm = normalize_text(theme)
        self.client.set(self._theme_key(chat_id), theme)
        try:
            self.client.set(f"{self._theme_key(chat_id)}:normalized", norm)
        except Exception:
            pass

    def increment_theme(self, theme: str) -> None:
        norm = normalize_text(theme)
        self.client.zincrby(self.THEME_STATS_KEY, 1, norm)
        try:
            self.client.sadd(f"{self.THEME_EXAMPLES_KEY}:{norm}", theme)
        except Exception:
            pass

    def get_top_themes(self, limit: int = 10) -> List[Dict[str, Any]]:
        res = self.client.zrevrange(THEME_STATS_KEY, 0, limit - 1, withscores=True)
        out: List[Dict[str, Any]] = []
        for theme_norm, score in res:
            examples = []
            try:
                members = list(
                    self.client.srandmember(
                        f"{THEME_EXAMPLES_KEY}:{theme_norm}", 5
                    )
                    or []
                )
                examples = [m for m in members if isinstance(m, str)]
            except Exception:
                examples = []
            out.append(
                {"normalized": theme_norm, "count": int(score), "examples": examples}
            )
        return out

    def clear_theme_stats(self) -> None:
        self.client.delete(THEME_STATS_KEY)

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
