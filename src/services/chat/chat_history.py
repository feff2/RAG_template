from typing import Dict, List, Optional

from transformers import AutoTokenizer

from src.llm.prompts import RAG_SYSTEM_PROMPT


class ChatHistory:
    def __init__(
        self, history: Optional[List[Dict[str, str]]] = None, max_tokens: int = 10000
    ) -> None:
        self.history = history or []
        self.max_tokens = max_tokens
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Thinking-2507")

    def add_system_message(self, message: str) -> None:
        self.history.append({"role": "system", "content": message})

    def add_user_message(self, message: str) -> None:
        self.history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        self.history.append({"role": "assistant", "content": message})

    def num_tokens(self) -> int:
        return sum(len(self.tokenizer.encode(msg["content"])) for msg in self.history)

    def truncate_by_tokens(self) -> None:
        truncated: List[Dict[str, str]] = []

        total_tokens = 0
        for msg in reversed(self.history):
            msg_tokens = len(self.tokenizer.encode(msg["content"]))
            if total_tokens + msg_tokens > self.max_tokens:
                break
            truncated.insert(0, msg)
            total_tokens += msg_tokens

        self.history = [{"role": "system", "content": RAG_SYSTEM_PROMPT}] + truncated
