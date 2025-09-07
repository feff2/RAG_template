import asyncio
import inspect
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.services.db.redis_chat_db import RedisChatDB

from .container import chat_engine, logger, settings
from .routers import common_questions_router, feedback_router, query_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("lifespan start")

    try:
        redis_chat_db = RedisChatDB(
            redis_url=settings.REDIS_URL,
            ttl=getattr(settings, "CHAT_TTL_SECONDS", 60 * 60 * 24),
        )
        setattr(chat_engine, "chat_db", redis_chat_db)
        app.state.redis_chat_db = redis_chat_db
        logger.info("RedisChatDB initialized and attached to chat_engine")
    except Exception as e:
        logger.exception("Failed to create RedisChatDB: %s", e)
    if inspect.iscoroutinefunction(chat_engine.start):
        await chat_engine.start()
    else:
        await asyncio.to_thread(chat_engine.start)

    app.state.chat_engine = chat_engine

    yield

    if inspect.iscoroutinefunction(chat_engine.close):
        await chat_engine.close()
    else:
        await asyncio.to_thread(chat_engine.close)

    try:
        if hasattr(app.state, "redis_chat_db") and app.state.redis_chat_db is not None:
            app.state.redis_chat_db.close()
            logger.info("RedisChatDB closed")
    except Exception as e:
        logger.exception("Error while closing RedisChatDB: %s", e)

    logger.info("lifespan end")


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    f"http://localhost:{settings.API_PORT}",
    f"http://127.0.0.1:{settings.API_PORT}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
router.include_router(common_questions_router, prefix=settings.API_V1_STR)
router.include_router(query_router, prefix=settings.API_V1_STR)
router.include_router(feedback_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def generic_exception_handler(
    request: Request,
    call_next: Callable[..., Any],
) -> JSONResponse:
    try:
        return await call_next(request)
    except Exception as err:  # noqa: BLE001
        logger.exception(err)
        return JSONResponse(
            content={"detail": "Internal Server Error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=exc.errors(),
    )


faq_router = APIRouter(prefix=settings.API_V1_STR)


@faq_router.get("/faq")
async def get_faq(request: Request, limit: int = 10) -> dict:
    redis_db = request.app.state.redis_chat_db
    return {"questions": redis_db.get_top_questions(limit)}


app.include_router(faq_router)
app.include_router(router=router)

app.mount("/", StaticFiles(directory="src/services/ui", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "src.services.api_gateway.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        access_log=False,
    )
