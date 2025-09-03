import torch
from typing import List
from .cross_encoder import CrossEncoder
from transformers import AutoTokenizer, AutoModel


class CrossEncoderTorch(CrossEncoder):
    def __init__(self: "CrossEncoderTorch", model_name: str, device: torch.device):
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = device
        self.model.to(device)
        self.model.eval()

    def rerank(self: "CrossEncoderTorch", pair: List[str]) -> List[float]:
        features = self.tokenizer(
            pair, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            return self.model(**features).logits
