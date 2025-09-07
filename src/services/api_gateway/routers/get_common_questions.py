from datetime import datetime
from typing import List

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from ..container import logger
from ..schemes import QuestionItem, QuestionsOut

router = APIRouter(tags=["common_questions"], include_in_schema=False)


async def __common_questions(request: Request, limit: int) -> QuestionsOut:
    try:
        redis_db = request.app.state.redis_chat_db
        raw = await run_in_threadpool(redis_db.get_top_questions, limit)

        items: List[QuestionItem] = []
        for r in raw:
            norm = r.get("normalized") if isinstance(r, dict) else None
            cnt = int(r.get("count", 0)) if isinstance(r, dict) else 0
            examples = r.get("examples") if isinstance(r, dict) else []
            items.append(
                QuestionItem(normalized=norm or "", count=cnt, examples=examples)
            )

        return QuestionsOut(
            generated_at=datetime.utcnow().isoformat() + "Z",
            limit=limit,
            results=items,
        )
    except Exception as e:
        logger.exception("Failed to get common questions: %s", e)
        raise


@router.get("/common_questions", response_model=QuestionsOut)
async def common_questions(
    request: Request, limit: int = Query(10, ge=1, le=200)
) -> None:
    return await __common_questions(request, limit)
