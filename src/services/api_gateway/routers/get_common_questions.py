from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from ..container import logger
from ..schemes import StatItem, StatOut

router = APIRouter(tags=["common_questions"], include_in_schema=False)


async def __common_questions(
    request: Request,
    limit: int,
    source: Literal["redis", "qdrant"] = "redis",
) -> StatOut:
    try:
        items: List[StatItem] = []

        if source == "redis":
            redis_db = request.app.state.redis_chat_db
            raw = await run_in_threadpool(redis_db.get_top_questions, limit)
            for r in raw:
                norm = r.get("normalized") if isinstance(r, dict) else None
                cnt = int(r.get("count", 0)) if isinstance(r, dict) else 0
                examples = r.get("examples") if isinstance(r, dict) else []
                items.append(
                    StatItem(normalized=norm or "", count=cnt, examples=examples)
                )

        elif source == "qdrant":
            qdrant_db = request.app.state.chat_engine.qdrant_chat_db
            raw = await run_in_threadpool(qdrant_db.top_normalized_phrases, limit)
            for norm, cnt in raw:
                examples = await run_in_threadpool(
                    qdrant_db.search_similar,
                    norm,
                    1,
                    True,
                )
                example_texts = []
                if examples:
                    payload = examples[0].get("payload", {})
                    txt = payload.get("text")
                    if txt:
                        example_texts.append(txt)
                items.append(
                    StatItem(normalized=norm, count=cnt, examples=example_texts)
                )

        else:
            raise ValueError(f"Unknown source '{source}'")

        return StatOut(
            generated_at=datetime.utcnow().isoformat() + "Z",
            limit=limit,
            results=items,
        )

    except Exception as e:
        logger.exception("Failed to get common questions: %s", e)
        raise


@router.get("/common_questions", response_model=StatOut)
async def common_themes(
    request: Request,
    limit: int = Query(10, ge=1, le=200),
    source: Literal["redis", "qdrant"] = Query("redis"),
):
    return await __common_questions(request, limit, source)
