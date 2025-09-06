from fastapi import APIRouter, HTTPException
from ..schemes import QueryIn, QueryOut
from ..container import logger, chat_engine
import traceback
import time
from starlette.concurrency import run_in_threadpool

router = APIRouter(tags=["process_query", "query"], include_in_schema=False)

async def __process_query(
    input_: QueryIn,
    session_id: str,
) -> QueryOut:
    q = input_
    try:
        generated = await run_in_threadpool(
            chat_engine.user_query, session_id, input_.query
        )
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            {
                "ts": time.time(),
                "request_id": input_.request_id,
                "error": str(e),
                "traceback": tb,
            }
        )
        raise HTTPException(status_code=500, detail="Query failed")
    return QueryOut(request_id=q.request_id, response=generated)


@router.post("/query")
async def process_query(input_: QueryIn) -> QueryOut:
    return await __process_query(input_, session_id="default_session_id")
