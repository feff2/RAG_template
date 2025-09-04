from fastapi import APIRouter


from ..schemes import CreateCollectionIn
from ..container import logger, service

router = APIRouter(tags=["encode", "bi_encoder"], include_in_schema=False)

async def __create_collection(
    input_: CreateCollectionIn,
) -> None:
    msg = f"Create collection with name {input_.name}"
    logger.debug(msg)

    await service.create_collection(
        collection_name=input_.name,
        vector_size=input_.vector_size,
        dense_vector_name=input_.dense_vector_name,
        sparse_vector_names=input_.sparse_vector_names,
        sparse_on_disk=input_.sparse_on_disk,
    )

    msg = f"Collection: {input_.name} created"
    logger.debug(msg)

    return

@router.post(
    f"/create_collection/",
    summary="Создать коллекцию в Qdrant",
)
async def create_collection(input_: CreateCollectionIn) -> None:
    await __create_collection(input_)
