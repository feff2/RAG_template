from src.services.chat.chat_engine import ChatEngine
from src.shared.logger import CustomLogger
from .settings import settings

chat_engine = ChatEngine()
logger = CustomLogger("api_gateway")
