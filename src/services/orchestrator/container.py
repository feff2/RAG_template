from src.shared.logger import CustomLogger
from .settings import settings
from .service import LLMOrchestrator

logger = CustomLogger("orchestrator")

service = LLMOrchestrator(
    service=settings.SERVICES,
    history_max_token=settings.HISTORY_MAX_TOKEN
)

