@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest, session_id: str = Depends(get_session)):
    try:
        # Передаем запрос оркестратору
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://orchestrator:8001/process",
                json={"query": request.query, "session_id": session_id}
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Orchestrator error")
        
        return JSONResponse(
            content={
                "response": response.json()["response"],
                "session_id": session_id
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))