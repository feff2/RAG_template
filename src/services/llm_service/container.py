from .service import LLMService
from .settings import settings
from src.shared.logger import CustomLogger


logger = CustomLogger("llm_service") 

llm_service = LLMService(
    model_name=settings.MODEL_NAME,
    max_concurrency = settings.MAX_CONCURENCY,
    request_timeout = settings.REQUEST_TIMEOUT,
    params = settings.PARAMS,
    system_prompt = settings.SYSTEM_PROMPT,
    batch_window_ms = settings.BATCH_WINDOW_MS,
    logger=logger,
    settings=settings
)
