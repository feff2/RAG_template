from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from src.api.dependencies import get_redis_client, get_session
from src.api.service import SessionService

router = APIRouter()

@router.post("/session/clear/{history_session}")
async def clear_session(history_session: str, redis=Depends(get_redis_client)):
    ss = SessionService(redis)
    await ss.clear_history(history_session)
    return {"ok": True}

@router.get("/session/{history_session}")
async def get_session_info(history_session: str, redis=Depends(get_redis_client)):
    ss = SessionService(redis)
    history = await ss.load_history(history_session)
    return {"session": history_session, "history_len": len(history) if history else 0}
