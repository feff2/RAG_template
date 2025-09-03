import torch

from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    INFERENCE_HOST: str = ""
    BI_ENCODER_PORT: int = 0
    CROSS_ENCODER_PORT: int = 0
    INFERENCE_TIMEOUT_S: int = 10
    MAX_QUEUE_DELAY_MICROSECONDS: int = 10
    MAX_BATCH_SIZE: int = 8
    GPU_INDEX: int = 0
    USE_GPU: bool = True if SharedSettings.DEVICE == torch.device("cuda") else "False"


settings = Settings()
