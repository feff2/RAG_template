from .service import VectorDbService
from src.shared.logger import CustomLogger
from .settings import settings


logger = CustomLogger("Vector_db")

service = VectorDbService(
    url=settings.URL, 
    logger=logger,
    settings=settings
)