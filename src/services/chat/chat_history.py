from typing import Dict, List, Optional


class ChatHistory:
    def __init__(self, history: Optional[List[Dict[str, str]]] = None, history_max_len: int = 10000) -> None:
        self.history = history or []
        self.history_max_len = history_max_len

    def add_system_message(self, message: str) -> None:
        self.history.append({"role": "system", "content": message})

    def add_user_message(self, message: str) -> None:
        self.history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        self.history.append({"role": "assistant", "content": message})

    def truncate_history(self) -> None:
        if len(self.history) <= self.history_max_len:
            return
        
        system_messages = [msg for msg in self.history if msg["role"] == "system"]
        non_system_messages = [msg for msg in self.history if msg["role"] != "system"]
        
        max_non_system = max(0, self.history_max_len - len(system_messages))
        truncated_non_system = non_system_messages[-max_non_system:] if max_non_system > 0 else []
        
        self.history = system_messages + truncated_non_system