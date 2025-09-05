from typing import Dict, List, Optional


class ChatHistory:
    def __init__(self, history: Optional[List[Dict[str, str]]] = None) -> None:
        self.history = history or []

    def add_system_message(self, message: str) -> None:
        self.history.append({"role": "system", "content": message})

    def add_user_message(self, message: str) -> None:
        self.history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        self.history.append({"role": "assistant", "content": message})
