# orchestrator.py
from fastapi import FastAPI, HTTPException
import httpx
import asyncio
from pydantic import BaseModel
from typing import List, Dict
import json
from datetime import datetime

app = FastAPI(title="RAG Orchestrator")

# Конфигурация сервисов
SERVICES = {
    "bi_encoder": "http://bi-encoder:8002/retrieve",
    "cross_encoder": "http://cross-encoder:8003/rerank", 
    "llm": "http://llm-service:8004/generate"
}

# Модели данных


# Кэш для хранения истории сессий (в production используйте Redis)
session_cache = {}

async def call_service(service_url: str, payload: dict, timeout: int = 30):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                service_url,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Service error: {str(e)}")


def format_context(documents: List[Dict]) -> str:
    return "\n".join([f"[{i+1}] {doc['text']}" for i, doc in enumerate(documents)])

def add_history_to_context(context: str, history: List[Dict]) -> str:
    if not history:
        return context
    
    history_text = "\n".join([
        f"Previous Q: {item['query']}\nPrevious A: {item['response']}" 
        for item in history[-3:]  # Последние 3 пары Q/A
    ])
    
    return f"Previous conversation:\n{history_text}\n\nCurrent context:\n{context}"

def update_session_history(session_id: str, query: str, response: str):
    if session_id not in session_cache:
        session_cache[session_id] = []
    
    session_cache[session_id].append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "response": response
    })
    
    # Ограничиваем историю последними 10 взаимодействиями
    if len(session_cache[session_id]) > 10:
        session_cache[session_id] = session_cache[session_id][-10:]

# Фоновая задача для очистки старых сессий
async def cleanup_sessions():
    while True:
        await asyncio.sleep(3600)  # Каждый час
        current_time = datetime.now()
        # Удаляем сессии без активности более 24 часов
        for session_id in list(session_cache.keys()):
            last_interaction = datetime.fromisoformat(
                session_cache[session_id][-1]["timestamp"]
            )
            if (current_time - last_interaction).total_seconds() > 86400:
                del session_cache[session_id]

