import torch

from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    INFERENCE_HOST: str = "localhost"
    BI_ENCODER_PORT: int = 9004
    CROSS_ENCODER_PORT: int = 9005
    
    BI_ENCODER_PATH: str = "/app/models/bi_encoder/all-MiniLM-L6-v2"
    CROSS_ENCODER_PATH: str = "/app/models/reranker/ms-marco-MiniLM-L6-v2"
    BI_ENCODER_NAME: str = "all_MiniLM_L6_v2"
    CROSS_ENCODER_NAME: str = "ms_marco_MiniLM_L6_v2"
    
    CROSS_ENCODER_FORMAT: str = "torch"
    BI_ENCODER_FORMAT: str = "torch"

    INFERENCE_TIMEOUT_S: int = 10
    MAX_QUEUE_DELAY_MICROSECONDS: int = 10
    MAX_BATCH_SIZE: int = 8
    GPU_INDEX: int = 0

    API_V1_STR: str = "/api/v1"

    USE_GPU: bool = True if torch.cuda.is_available else False


settings = Settings()
