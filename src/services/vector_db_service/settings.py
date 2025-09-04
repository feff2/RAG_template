import os
from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    API_V1_STR: str = "/api/v1"
    URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")