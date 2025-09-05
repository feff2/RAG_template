from typing import ClassVar, Dict

from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    HISTORY_MAX_TOKEN: int = 1000
    SERVICES: ClassVar[Dict[str, str]] = {
        "db": "localhost:6333/api/v1/search", 
        "bi_encoder": "localhost:9004/api/v1/retrieve", 
        "cross_encoder": "localhost:9005/api/v1/rerank",
        "llm": "localhost:8004/api/v1/generate",
    }
    API_PORT: int = 9000
    ORCHESTRATOR_PORT: int = 9001
    ORCHESTRATOR_HOST: str = "localhost"

settings = Settings()