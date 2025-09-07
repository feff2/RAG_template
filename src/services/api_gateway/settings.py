from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    HISTORY_MAX_TOKEN: int = 1000
    API_HOST: str = "localhost"
    API_PORT: int = 8080
    RELOAD: bool = True
    API_V1_STR: str = "/api/v1"
    REDIS_URL: str = "redis://localhost:6379/0"
    EMBEDING_MODEL_DIM: int = 384
    QDRANT_URL: str = "http://localhost:6333"


settings = Settings()
