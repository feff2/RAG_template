from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import probes_router, process_query_router
from .container import server, client, logger, settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("lifespan start")
    yield
    logger.info("lifespan end")


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

router = APIRouter()
router.include_router(probes_router)

router.include_router(process_query_router, prefix=settings.API_V1_STR)

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
        "src.services.orchestrator.main:app",
        host="0.0.0.0",  # noqa: S104
        port=settings.API_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        access_log=False,
    )