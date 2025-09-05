from fastapi import APIRouter


from ..schemes import QueryIn, QueryOut
from ..container import logger, client

router = APIRouter(tags=["process_query", "orchestrator"], include_in_schema=False)

async def __process_query(
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
    f"/process_query/",
    summary="",
)
async def predict(input_: EncodeIn) -> EncodeOut:
    return await __process_query(input_)
