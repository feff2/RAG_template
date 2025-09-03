import torch

from pydantic_settings import BaseSettings, Field


class SharedSettings(BaseSettings):
    LOGGING_LEVEL: int = Field(20, description="logging level (numeric)")
    DEBUG: bool = Field(False, description="turn on debug mode (more verbose)")

    DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_availiable else "cpu")
    SEED: int = 42


settings = SharedSettings()
