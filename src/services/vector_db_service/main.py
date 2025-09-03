# main.py
import os
import logging
from logging.config import dictConfig

import uvicorn


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"fmt": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": LOG_LEVEL,
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)


def get_settings():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("DEV", "false").lower() in ("1", "true", "yes")
    workers_env = os.getenv("WORKERS")
    workers = int(workers_env) if workers_env else None
    return host, port, reload, workers


if __name__ == "__main__":
    host, port, reload, workers = get_settings()

    logger.info(
        "Starting app with host=%s port=%s reload=%s workers=%s",
        host,
        port,
        reload,
        workers,
    )

    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level=LOG_LEVEL.lower(),
        workers=workers or 1,
    )
