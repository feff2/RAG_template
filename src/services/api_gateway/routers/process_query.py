import re
import time
import asyncio
import traceback

import pymorphy3
from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from ..container import chat_engine, logger
from ..schemes import QueryIn, QueryOut

OPERATOR_TEMPLATE = (
    "Добрый день! Ваш запрос требует внимания специалиста или не относится к теме госзакупок. "
    "Пожалуйста, перейдите в [чат поддержки](https://t.me/RoseltorgCPP_bot), если считаете, что запрос релевантен."
    "Спасибо!"
)

_morph = pymorphy3.MorphAnalyzer()


def normalize_text(text: str) -> str:
    if not text:
        return ""
    tokens = re.findall(r"\w+", text.lower())
    lemmas = []
    for t in tokens:
        try:
            lemmas.append(_morph.parse(t)[0].normal_form)
        except Exception:
            lemmas.append(t)
    return " ".join(lemmas)


router = APIRouter(tags=["process_query", "query"], include_in_schema=False)


async def __process_query(
    request: Request,
    input_: QueryIn,
) -> QueryOut:
    q = input_
    try:
        text, docs = await asyncio.wait_for(
            run_in_threadpool(chat_engine.user_query, input_.user_id, input_.query),
            timeout=300.0
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

    redis_db = request.app.state.redis_chat_db
    history = redis_db.get_chat(q.user_id)
    theme = redis_db.get_theme(q.user_id)
    logger.info(f"History len: {len(history.history)}")

    if len(history.history) >= 0 and not theme:
        theme = await run_in_threadpool(chat_engine.gen_main_theme, history)
        redis_db.save_theme(q.user_id, theme)
        norm_theme = normalize_text(theme)
        try:
            redis_db.client.zincrby("chat:stats:themes", 1, norm_theme)
            redis_db.client.sadd(f"chat:stats:themes:examples:{norm_theme}", theme)
        except Exception as e:
            logger.warning(f"Failed to save theme stats: {e}")

        qdrant_db = request.app.state.chat_engine.qdrant_chat_db
        try:
            vector = await run_in_threadpool(chat_engine.embed_text, theme)
            qdrant_db.upsert_theme(norm_theme, theme, vector)
        except Exception as e:
            logger.warning(f"Failed to save theme to Qdrant: {e}")

    else:
        theme = theme if theme else None

    logger.info(f"Theme: {theme}")

    return QueryOut(user_id=q.user_id, response=final_response, theme=theme)


@router.post("/query")
async def process_query(request: Request, input_: QueryIn) -> QueryOut:
    return await __process_query(request, input_)
