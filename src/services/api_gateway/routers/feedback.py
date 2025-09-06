@router.post("/feedback")
async def submit_feedback(f: FeedbackIn, redis=Depends(get_redis_client)):
    session_service = SessionService(redis)
    await session_service.add_feedback({"request_id": f.request_id, "session": f.history_session, "feedback": f.feedback, "ts": time.time()})
    return {"ok": True}
