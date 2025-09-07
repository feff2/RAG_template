from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from ..container import logger
from ..schemes import StatItem, StatOut

router = APIRouter(tags=["common_themes"], include_in_schema=False)


async def __common_themes(
    request: Request,
    limit: int,
    source: Literal["redis", "qdrant"] = "redis",
) -> StatOut:
    try:
        items: List[StatItem] = []

        redis_db = request.app.state.redis_chat_db
        raw = await run_in_threadpool(redis_db.get_top_themes, limit)
        for r in raw:
            norm = r.get("normalized") if isinstance(r, dict) else None
            cnt = int(r.get("count", 0)) if isinstance(r, dict) else 0
            examples = r.get("examples") if isinstance(r, dict) else []
            items.append(StatItem(normalized=norm or "", count=cnt, examples=examples))

        return StatOut(
            generated_at=datetime.utcnow().isoformat() + "Z",
            limit=limit,
            results=items,
        )

    except Exception as e:
        logger.exception("Failed to get common themes: %s", e)
        raise


@router.get("/common_themes", response_model=StatOut)
async def common_themes(
    request: Request,
    limit: int = Query(10, ge=1, le=200),
    source: Literal["redis"] = Query("redis"),
):
    return await __common_themes(request, limit, source)
