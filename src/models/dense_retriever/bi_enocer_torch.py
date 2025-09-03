from typing import List
import torch
from transformers import AutoTokenizer, AutoModel
from src.models.dense_retriever.bi_encoder import BiEncoder
from src.shared.settings import settings


class BiEncoderTorch(BiEncoder):
    def __init__(
        self: "BiEncoderTorch",
        model_name: str,
        max_length: int = 512,
        device: torch.device = None,
    ):
        device = device or settings.DEVICE
        super().__init__(model_name, max_length)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = device
        self.model.to(device)
        self.model.eval()

    @staticmethod
    def _mean_pooling(model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def encode(self: "BiEncoderTorch", texts: List[str]) -> torch.Tensor:
        if not texts:
            return torch.zeros((0, 0), dtype=torch.float32).to(self.device)

        encoded_input = self.tokenizer(
            texts, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            model_output = self.model(**encoded_input.to(self.device))

        sentence_embeddings = self._mean_pooling(
            model_output, encoded_input["attention_mask"]
        )

        return sentence_embeddings
