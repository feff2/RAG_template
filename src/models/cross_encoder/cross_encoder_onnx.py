import torch


from .cross_encoder import CrossEncoder
from src.shared.settings import settings


class CrossEncoderOnnx(CrossEncoder):
    def __init__(
        self: "CrossEncoderOnnx",
        model_name: str,
        max_length: int = 512,
        device: torch.device = None,
    ):
        device = device or settings.DEVICE
        super().__init__(model_name, max_length)
