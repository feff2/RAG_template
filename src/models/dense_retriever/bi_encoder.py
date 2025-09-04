import torch

from abc import ABC, abstractmethod
from typing import Sequence, Union
import numpy as np
from transformers import AutoTokenizer, AutoModel


class BiEncoder(ABC):
    """
    Абстрактный базовый класс для Bi-Encoder'ов.
    """

    def __init__(
        self, model_name: str, max_length: int = 512, device: torch.device = None
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = device
        self.model.to(device)
        self.model.eval()

    @abstractmethod
    def encode(
        self, texts: Sequence[str], batch_size: int = 32, normalize: bool = True
    ) -> np.ndarray:
        pass
