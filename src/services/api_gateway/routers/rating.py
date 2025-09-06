@router.post("/rating")
async def submit_rating(payload: RatingIn, redis=Depends(get_redis_client)):
    if not (1 <= payload.rating <= 5):
        raise HTTPException(status_code=400, detail="rating must be 1..5")
    session_service = SessionService(redis)
    await session_service.add_rating(payload.history_session, payload.rating)
    if payload.comment:
        await session_service.add_feedback({"request_id": payload.request_id, "session": payload.history_session, "comment": payload.comment, "ts": time.time()})
    return {"ok": True}


@router.get("/rating/average/{history_session}")
async def rating_average(history_session: str, redis=Depends(get_redis_client)):
    session_service = SessionService(redis)
    res = await session_service.get_rating_average(history_session)
    if not res:
        return {"session": history_session, "count": 0, "average": None}
    return {"session": history_session, **res}