from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import httpx

from .routers import process_router
from .settings import settings
from .service import OrchestratorService

class CustomLogger:
    def __init__(self, name):
        self.name = name
    
    def info(self, msg):
        print(f"[INFO] {self.name}: {msg}")
    
    def warning(self, msg):
        print(f"[WARN] {self.name}: {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {self.name}: {msg}")
    
    def exception(self, msg):
        print(f"[EXCEPTION] {self.name}: {msg}")

logger = CustomLogger("Orchestrator")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan start")
    
    # Инициализация сервиса оркестратора
    app.state.orchestrator_service = OrchestratorService(
        bi_encoder_url=settings.BI_ENCODER_URL,
        cross_encoder_url=settings.CROSS_ENCODER_URL,
        llm_service_url=settings.LLM_SERVICE_URL
    )
    
    # Проверка доступности всех сервисов
    services = {
        "Bi-Encoder": settings.BI_ENCODER_URL,
        "Cross-Encoder": settings.CROSS_ENCODER_URL,
        "LLM Service": settings.LLM_SERVICE_URL
    }
    
    for service_name, service_url in services.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code != 200:
                    logger.error(f"{service_name} health check failed")
                else:
                    logger.info(f"{service_name} is available")
        except Exception as e:
            logger.error(f"{service_name} connection failed: {str(e)}")
    
    yield
    
    # Завершение работы
    logger.info("Lifespan end")

app = FastAPI(
    title="RAG Orchestrator",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

router = APIRouter()
router.include_router(process_router, prefix=settings.API_V1_STR)

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
        "orchestrator.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.WORKERS,
        loop="uvloop",
        reload=settings.RELOAD,
        access_log=settings.ACCESS_LOG,
    )