from fastapi import APIRouter


from ..schemes import EncodeIn, EncodeOut
from ..container import logger, client

router = APIRouter(tags=["encode", "bi_encoder"], include_in_schema=False)

async def __encode(
    input_: EncodeIn,
) -> EncodeOut:
    msg = f"Encode request_id={input_.request_id}, text={input_.text[:100]}"
    logger.debug(msg)

    vectors = await client.encode(
        input_.request_id,
        input_.text,
    )

    msg = f"Vectors request_id={vectors}"
    logger.debug(msg)

    return EncodeOut(
        request_id=input_.request_id,
        vectors=vectors,
    )

@router.post(
    f"/encode/",
    summary="Получить вектор текста",
)
async def predict(input_: EncodeIn) -> EncodeOut:
    return await __encode(input_)
