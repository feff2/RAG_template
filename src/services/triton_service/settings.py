import torch

from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    INFERENCE_HOST: str = "localhost"
    BI_ENCODER_PORT: int = 9004
    CROSS_ENCODER_PORT: int = 9005
    
    BI_ENCODER_NAME: str = "models/bi_encoder/all-MiniLM-L6-v2"
    CROSS_ENCODER_NAME: str = "models/reranker/ms-marco-MiniLM-L6-v2"

    INFERENCE_TIMEOUT_S: int = 10
    MAX_QUEUE_DELAY_MICROSECONDS: int = 10
    MAX_BATCH_SIZE: int = 8
    GPU_INDEX: int = 0

    USE_GPU: bool = True if SharedSettings.DEVICE == torch.device("cuda") else "False"


settings = Settings()
