from typing import ClassVar, Dict
from src.shared.settings import SharedSettings

class Settings(SharedSettings):
    MODEL_NAME: str = "models/llm/Qwen3-1.7B"
    MAX_CONCURENCY: int = 100
    REQUEST_TIMEOUT: int = 10 
    PARAMS: ClassVar[Dict] = {"top_k": 100, "temperature": 1.0}
    SYSTEM_PROMPT: str = "Ты опытный и точный ассистент, который обращает огромное внимание на контекст, который получает. В случае если ты неуверен в ответе, скажи пользователю: 'Извините, я не могу помочь с этим вопросом, но готов ответить на другие'."
    BATCH_WINDOW_MS:int = 1000