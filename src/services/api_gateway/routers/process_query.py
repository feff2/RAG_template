import time
import traceback

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from ..container import chat_engine, logger
from ..schemes import QueryIn, QueryOut

OPERATOR_TEMPLATE = (
    "Добрый день! Ваш запрос требует внимания специалиста или не относится к теме госзакупок. "
    "Пожалуйста, перейдите в [чат поддержки](https://t.me/RoseltorgCPP_bot), если считаете, что запрос релевантен."
    "Спасибо!"
)


router = APIRouter(tags=["process_query", "query"], include_in_schema=False)


async def __process_query(
    input_: QueryIn,
) -> QueryOut:
    q = input_
    try:
        text, docs = await run_in_threadpool(
            chat_engine.user_query, input_.user_id, input_.query
        )
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            {
                "ts": time.time(),
                "request_id": input_.user_id,
                "error": str(e),
                "traceback": tb,
            }
        )
        raise HTTPException(status_code=500, detail="Query failed")

    if "[ОПЕРАТОР]" in text:
        logger.info(
            {
                "ts": time.time(),
                "request_id": input_.user_id,
                "event": "operator_token_detected",
            }
        )
        final_response = (OPERATOR_TEMPLATE, docs)
    else:
        final_response = (text, docs)

    return QueryOut(user_id=q.user_id, response=final_response)


@router.post("/query")
async def process_query(input_: QueryIn) -> QueryOut:
    return await __process_query(input_)
