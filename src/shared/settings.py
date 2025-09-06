from pydantic import Field
from pydantic_settings import BaseSettings


class SharedSettings(BaseSettings):
    LOGGING_LEVEL: int = Field(20, description="logging level (numeric)")
    DEBUG: bool = Field(False, description="turn on debug mode (more verbose)")
    SEED: int = 42


settings = SharedSettings()