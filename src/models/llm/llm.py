from abc import ABC, abstractmethod
from typing import List, Dict, Union
import torch
from transformers import AutoTokenizer


class Llm(ABC):
    def __init__(
        self,
        model_name: str,
        device: torch.device,
        params: dict,
        system_prompt: str,
        history_max_tokens: int,
    ):
        self.model_name = model_name
        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B", use_fast=True)
        self.system_prompt = system_prompt or ""
        self.params = params or {}
        self.history: List[Dict[str, str]] = []
        self.history_max_tokens = int(history_max_tokens)

        if self.tokenizer.pad_token is None:
            if self.tokenizer.eos_token is not None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            else:
                self.tokenizer.add_special_tokens({"pad_token": "<|pad|>"})

    @abstractmethod
    def generate(self, context: str, query: str) -> str:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass