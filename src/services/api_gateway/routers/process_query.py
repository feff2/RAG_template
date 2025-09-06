import re
import time
import traceback

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from ..container import chat_engine, logger
from ..schemes import QueryIn, QueryOut

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

    numbers = re.findall(r"\[(\d+)\]", text)

    return QueryOut(user_id=q.user_id, response=(text, [docs[n] for n in numbers]))


@router.post("/query")
async def process_query(input_: QueryIn) -> QueryOut:
    return await __process_query(input_)
