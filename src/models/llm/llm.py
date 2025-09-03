from abc import ABC, abstractmethod
from typing import List, Dict, Union
import torch
from transformers import AutoTokenizer


class Llm(ABC):
    def __init__(
        self,
        model_name: str,
        device: Union[str, torch.device],
        params: dict,
        system_prompt: str,
        history_max_tokens: int,
    ):
        self.model_name = model_name
        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.system_prompt = system_prompt or ""
        self.params = params or {}
        self.history: List[Dict[str, str]] = []
        self.history_max_tokens = int(history_max_tokens)

        if self.tokenizer.pad_token is None:
            if self.tokenizer.eos_token is not None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            else:
                self.tokenizer.add_special_tokens({"pad_token": "<|pad|>"})

    def _build_prompt(self, query: str, context: str) -> str:
        history_text = "\n".join([f"{h['role']}: {h['content']}" for h in self.history])
        return f"{self.system_prompt}\n{history_text}\n{context}\nuser: {query}\nassistant:"

    def _update_history(self, query: str, answer: str) -> None:
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": answer})

        enc = self.tokenizer(
            " ".join([h["content"] for h in self.history]), return_tensors="pt"
        )
        total_tokens = enc["input_ids"].shape[1]

        while total_tokens > self.history_max_tokens and len(self.history) > 2:
            self.history.pop(0)
            self.history.pop(0)
            enc = self.tokenizer(
                " ".join([h["content"] for h in self.history]), return_tensors="pt"
            )
            total_tokens = enc["input_ids"].shape[1]

    def _truncate_to_fit(self, text: str, max_new_tokens: int):
        return self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.history_max_tokens - max_new_tokens,
        )

    @abstractmethod
    def generate(self, context: str, query: str) -> str:
        pass

    @abstractmethod
    def load(self) -> None:
        pass
