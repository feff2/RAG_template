@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_sessions())