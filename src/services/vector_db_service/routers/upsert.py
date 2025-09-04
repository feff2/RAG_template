from fastapi import APIRouter


from ..schemes import UpsertIn
from ..container import logger, service

router = APIRouter(tags=["encode", "bi_encoder"], include_in_schema=False)

async def __upsert(
    inputs_: list[UpsertIn],
) -> None:
    
    for i, input_ in enumerate(inputs_):

        result = await service.upsert_points(
            collection_name=input_.collection_name,
            points=input_.vector,
        )
        if result:
            msg = f"Upserted {i} vector / {len(inputs_)}"
            logger.debug(msg)

    msg = f"Succesfully upserted all vectors"
    logger.debug(msg)
    
    return 

@router.post(
    f"/upsert/",
    summary="Добавление документов в БД",
)
async def upsert(input_: list[UpsertIn]) -> None:
    await __upsert(input_)
