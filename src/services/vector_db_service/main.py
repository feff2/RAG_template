from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import probes_router, info_router, upsert_router, search_router, create_collection_router

from .container import service, logger, settings



@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("lifespan start")
    await service.start()
    yield
    await service.close()
    logger.info("lifespan end")


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

router = APIRouter()
router.include_router(probes_router)

router.include_router(info_router, prefix=settings.API_V1_STR)
router.include_router(upsert_router, prefix=settings.API_V1_STR)
router.include_router(search_router, prefix=settings.API_V1_STR)
router.include_router(create_collection_router, prefix=settings.API_V1_STR)

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
        "src.services.vector_db_service.main:app",
        host="0.0.0.0",  # noqa: S104
        port=settings.API_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        access_log=False,
    )