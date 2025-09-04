from fastapi import APIRouter


from ..schemes import SearchIn, SearchOut
from ..container import logger, service

router = APIRouter(tags=["encode", "bi_encoder"], include_in_schema=False)

async def __search(
    input_: SearchIn,
) -> list[SearchOut]:
    msg = f"Create collection with name {input_.name}"
    logger.debug(msg)

    result = await service.hybrid_search(
        collection_name=input_.collection_name,
        query_dense=input_.query_dense,
        query_sparse=input_.query_sparse,
        sparse_name=input_.sparse_name,
        top_k=input_.top_k,
        prefetch_k=input_.prefetch_k,
        weight_dense=input_.weight_dense,
        weight_sparse=input_.weight_sparse,
        rrf_k=input_.rrf_k,
        with_payload=input_.with_payload,
    )

    msg = f"Collection: {input_.name} created"
    logger.debug(msg)
    
    return [SearchOut(
            id=res.id,
            rrf_score=res.rrf_score,
            payloadres=res.payloadres,
            score_dense=res.score_dense,
            score_sparse=res.score_sparse,
        ) for res in result]

@router.post(
    f"/search/",
    summary="Поиск релевантных документов",
)
async def search(input_: SearchIn) -> list[SearchOut]:
    await __search(input_)
