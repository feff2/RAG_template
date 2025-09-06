@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    session_data = await redis_client.get(f"session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return JSONResponse(content=json.loads(session_data))