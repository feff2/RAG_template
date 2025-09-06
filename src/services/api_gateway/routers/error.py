@router.get("/critical_errors")
async def critical_errors(limit: int = 50, redis=Depends(get_redis_client)):
    session_service = SessionService(redis)
    rows = await session_service.get_critical_errors(limit)
    return {"count": len(rows), "errors": rows}