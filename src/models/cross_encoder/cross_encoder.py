import torch
from abc import ABC, abstractmethod
from typing import List
from transformers import AutoTokenizer, AutoModel


class CrossEncoder(ABC):
    def __init__(self: "CrossEncoder", model_name: str, device: torch.device):
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = device
        self.model.to(device)
        self.model.eval()

    @abstractmethod
    def rerank(self: "CrossEncoder", pairs: List[str]) -> List[float]:
        pass
