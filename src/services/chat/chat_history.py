from typing import Dict, List, Optional

from transformers import AutoTokenizer


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
        total_tokens = 0
        for msg in self.history:
            total_tokens += len(self.tokenizer.encode(msg["content"]))
        return total_tokens

    def truncate_by_tokens(self) -> None:
        system_messages = [msg for msg in self.history if msg["role"] == "system"]
        non_system_messages = [msg for msg in self.history if msg["role"] != "system"]

        truncated_non_system = []
        total_tokens = sum(
            len(self.tokenizer.encode(msg["content"])) for msg in system_messages
        )

        for msg in reversed(non_system_messages):
            msg_tokens = len(self.tokenizer.encode(msg["content"]))
            if total_tokens + msg_tokens > self.max_tokens:
                continue
            truncated_non_system.insert(0, msg)
            total_tokens += msg_tokens

        self.history = system_messages + truncated_non_system
