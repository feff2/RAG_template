from logging import Logger, Formatter, StreamHandler
import sys

from src.shared.settings import settings


class CustomLogger(Logger):
    def __init__(self, name, level=settings.LOGGING_LEVEL):
        super().__init__(name, level)
        self._setup_handlers()

    def _setup_handlers(self):
        handler = StreamHandler(sys.stdout)
        formatter = Formatter("%(levelname)s - %(name)s - %(asctime)s  - %(message)s")
        handler.setFormatter(formatter)
        self.addHandler(handler)