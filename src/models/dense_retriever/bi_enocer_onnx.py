import torch


from .bi_encoder import BiEncoder
from src.shared.settings import settings


class BiEncoderOnnx(BiEncoder):
    def __init__(
        self: "BiEncoderOnnx",
        model_name: str,
        max_length: int = 512,
        device: torch.device = None,
    ):
        device = device or settings.DEVICE
        super().__init__(model_name, max_length)
