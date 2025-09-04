from fastapi import APIRouter


from ..schemes import RerankIn, RerankOut
from ..container import logger, client

router = APIRouter(tags=["rerank", "cross_encoder"], include_in_schema=False)

async def __rerank(
    input_: RerankIn,
) -> RerankOut:
    msg = f"Score request_id={input_.request_id}, text={input_.pairs[0][0][:100]}"
    logger.debug(msg)

    scores = await client.rerank(
        input_.request_id,
        input_.pairs,
    )

    msg = f"Scores request_id={scores}"
    logger.debug(msg)

    return RerankOut(
        request_id=input_.request_id,
        scores=scores,
    )

@router.post(
    f"/rerank/",
    summary="Получить скоры для пар текстов",
)
async def predict(input_: RerankIn) -> RerankOut:
    return await __rerank(input_)
