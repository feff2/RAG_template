from fastapi import APIRouter

from ..schemes import InfoOut
from ..container import service, logger


router = APIRouter(tags=["info", "vector-db"], include_in_schema=False)

async def __get_info() -> InfoOut:
    msg = "Get Qdrant database info"
    logger.debug(msg)
    
    info = await service.get_info()
    
    return InfoOut(
        started=info["started"],
        collections=info["collections"],
        sparse_dim=info["sparse_dim"],
        dense_dim=info["dense_dim"],
        url=service.url
    )


@router.get(
    "/info/",
    summary="Получить информацию о Qdrant базе данных",
    response_model=InfoOut
)
async def get_vector_db_info() -> InfoOut:
    return await __get_info()
