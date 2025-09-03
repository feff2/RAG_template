# api_gateway.py
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import uuid
import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI(title="RAG API Gateway")

# Конфигурация Redis для хранения сессий
redis_client = redis.from_url(REDIS_URL)

# Модели запросов/ответов

# Зависимость для получения сессии
async def get_session(session_id: str = None):
    if not session_id:
        # Создаем новую сессию
        session_id = str(uuid.uuid4())
        await redis_client.setex(
            f"session:{session_id}", 
            timedelta(minutes=30),  # TTL 30 минут
            json.dumps({"created_at": datetime.now().isoformat()})
        )
    else:
        # Проверяем существующую сессию
        session_data = await redis_client.get(f"session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        # Обновляем TTL сессии
        await redis_client.expire(f"session:{session_id}", timedelta(minutes=30))
    
    return session_id

# Фоновая задача для очистки старых сессий
async def cleanup_sessions():
    while True:
        await asyncio.sleep(3600)  # Каждый час
        # Удаляем сессии старше 24 часов
        async for key in redis_client.scan_iter("session:*"):
            ttl = await redis_client.ttl(key)
            if ttl < 0:  # Истекший TTL
                await redis_client.delete(key)
