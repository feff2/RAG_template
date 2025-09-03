from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import probes_router, rerank_router, encode_router
from .triton_server import TritonClient, TritonServer
from .settings import settings

from src.models.dense_retriever.bi_enocer_torch import BiEncoderTorch
from src.models.dense_retriever.bi_enocer_onnx import BiEncoderOnnx
from src.models.cross_encoder.cross_encoder_torch import CrossEncoderTorch
from src.models.cross_encoder.cross_encoder_onnx import CrossEncoderOnnx
from src.shared.logger import CustomLogger

logger = CustomLogger("Triton main")

if settings.cross_encoder_format == "torch":
    cross_encoder = CrossEncoderTorch(
        model_name=settings.CROSS_ENCODER_NAME,
        device=settings.DEVICE,
    )
else:
    cross_encoder = CrossEncoderOnnx(
        model_name=settings.CROSS_ENCODER_NAME,
        device=settings.DEVICE,
    )

if settings.bi_encoder_format == "torch":
    bi_encoder = BiEncoderTorch(
        model_name=settings.BI_ENCODER_NAME,
        device=settings.DEVICE,
    )
else:
    bi_encoder = BiEncoderOnnx(
        model_name=settings.BI_ENCODER_NAME,
        device=settings.DEVICE,
    )

client = TritonClient(
    inference_host=settings.INFERENCE_HOST,
    bi_encoder_port=settings.BI_ENCODER_PORT,
    cross_encoder_port=settings.CROSS_ENCODER_PORT,
    inference_timeout_s=settings.INFERENCE_TIMEOUT_S,
    bi_encoder_name=settings.BI_ENCODER_NAME,
    cross_encoder_name=settings.CROSS_ENCODER_NAME,
    device=settings.DEVICE,
)

server = TritonServer(
    bi_encoder=bi_encoder,
    cross_encoder=cross_encoder,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("lifespan start")
    server.run()
    yield
    await server.close()
    logger.info("lifespan end")


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

router = APIRouter()
router.include_router(probes_router)

router.include_router(rerank_router, prefix=settings.API_V1_STR)
router.include_router(encode_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def generic_exception_handler(  # pyright: ignore[reportUnusedFunction]
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

app.include_router(router=router)


if __name__ == "__main__":
    uvicorn.run(
        "src.services.triton_service.main:app",
        host="0.0.0.0",  # noqa: S104
        port=settings.API_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        access_log=False,
    )