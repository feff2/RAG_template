from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import httpx
import redis.asyncio as redis

from .routers import query_router, session_router
from .settings import settings
from .dependencies import get_redis_client, get_session
from .service import SessionService

logger = CustomLogger("API Gateway")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan start")
    
    app.state.redis_client = redis.from_url(settings.REDIS_URL)
    
    app.state.session_service = SessionService(app.state.redis_client)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ORCHESTRATOR_URL}/health")
            if response.status_code != 200:
                logger.error("Orchestrator health check failed")
            else:
                logger.info("Orchestrator is available")
    except Exception as e:
        logger.error(f"Orchestrator connection failed: {str(e)}")
    
    yield
    
    await app.state.redis_client.close()
    logger.info("Lifespan end")

app = FastAPI(
    title="RAG API Gateway",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

router = APIRouter()
router.include_router(query_router, prefix=settings.API_V1_STR)
router.include_router(session_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def generic_exception_handler(
    request: Request,
    call_next: Callable[..., Any],
) -> JSONResponse:
    try:
        return await call_next(request)
    except Exception as err:
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

app.include_router(router=router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "api_gateway.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.WORKERS,
        loop="uvloop",
        reload=settings.RELOAD,
        access_log=settings.ACCESS_LOG,
    )