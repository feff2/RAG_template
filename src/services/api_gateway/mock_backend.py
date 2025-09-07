"""
Mock backend для тестирования фронтенда
Простые ответы без реальной обработки
"""

import asyncio
import random
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# Модели данных
class QueryIn(BaseModel):
    user_id: str
    query: str


class QueryOut(BaseModel):
    user_id: str
    response: tuple[str, list[str]]
    theme: Optional[str]


class FeedbackIn(BaseModel):
    user_id: str
    user_message: str
    model_response: str
    rating: int
    feedback: Optional[str]


# FastAPI приложение
app = FastAPI(
    title="Mock Backend для RAG Template",
    description="Простой mock сервер для тестирования фронтенда",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)

# CORS настройки
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock источники
MOCK_SOURCES = [
    "https://www.roseltorg.ru/knowledge_db/azbuka-zakupok/torgi",
    "https://www.roseltorg.ru/knowledge_db/trebovaniya-k-uchastnikam-zakupok",
    "https://www.roseltorg.ru/knowledge_db/docs/documents",
    "https://www.roseltorg.ru/_flysystem/webdav/2025/08/25/rp_corp_25082025.pdf",
]

# Счетчик запросов для определения темы
request_count = {}


@app.post("/api/v1/query")
async def process_query(query_data: QueryIn) -> QueryOut:
    """
    Mock обработка запроса - возвращает промпт обратно как ответ
    На третий запрос добавляет тему
    """
    # Имитация задержки обработки
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Подсчет запросов для пользователя
    user_id = query_data.user_id
    if user_id not in request_count:
        request_count[user_id] = 0
    request_count[user_id] += 1

    # Создаем mock ответ на основе промпта
    user_query = query_data.query

    # Формируем ответ в markdown формате
    mock_response = f"""### **Ответ на ваш вопрос**

Вы спросили: "{user_query}"

---

Это **mock ответ** для тестирования системы. В реальной системе здесь был бы \
развернутый ответ от ИИ модели с анализом документов и источников.

#### **Основные моменты:**
- Ваш запрос получен и обработан
- Система работает корректно
- Markdown форматирование поддерживается
- Источники отображаются как [1], [2], [3]

Для получения реальных ответов подключите основной backend.

**Источники информации:** [1] [2] [3]"""

    # Определяем тему (с 3-го запроса)
    theme = None
    if request_count[user_id] >= 3:
        # Используем промпт как тему (обрезаем если слишком длинный)
        theme = user_query[:100] + "..." if len(user_query) > 100 else user_query

    # Случайно выбираем источники
    sources = random.sample(MOCK_SOURCES, k=random.randint(2, 4))

    return QueryOut(user_id=user_id, response=(mock_response, sources), theme=theme)


@app.post("/api/v1/feedback")
async def submit_feedback(feedback_data: FeedbackIn) -> Dict[str, bool]:
    """
    Mock обработка обратной связи - всегда возвращает успех
    """
    # Валидация рейтинга
    if not (1 <= feedback_data.rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Рейтинг должен быть от 1 до 5",
        )

    # Имитация обработки
    await asyncio.sleep(0.2)

    # Логируем для отладки
    print(f"📝 Получен отзыв от пользователя {feedback_data.user_id}")
    print(f"⭐ Рейтинг: {feedback_data.rating}/5")
    print(f"💬 Сообщение пользователя: {feedback_data.user_message[:50]}...")
    print(f"🤖 Ответ модели: {feedback_data.model_response[:50]}...")
    if feedback_data.feedback:
        print(f"📋 Дополнительный отзыв: {feedback_data.feedback}")
    print("---")

    return {"ok": True}


@app.get("/api/v1/faq")
async def get_faq(limit: int = 10) -> Dict[str, list]:
    """
    Mock FAQ - возвращает примеры вопросов
    """
    mock_questions = [
        "Как участвовать в электронных торгах?",
        "Какие документы нужны для регистрации?",
        "Как подать заявку на участие в закупке?",
        "Что такое квалификационный отбор?",
        "Как работает электронная подпись?",
    ]

    return {"questions": mock_questions[:limit]}


@app.get("/api/v1/health")
async def health_check():
    """Проверка работоспособности сервера"""
    return {
        "status": "ok",
        "message": "Mock backend работает",
        "active_users": len(request_count),
        "total_requests": sum(request_count.values()),
    }


# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"❌ Ошибка в mock backend: {exc}")
    return JSONResponse(
        status_code=500, content={"detail": "Внутренняя ошибка сервера"}
    )


# Статические файлы (фронтенд)
app.mount("/", StaticFiles(directory="src/services/ui", html=True), name="static")


if __name__ == "__main__":
    print("🚀 Запуск Mock Backend...")
    print("📡 API: http://127.0.0.1:8080/api/docs")
    print("🎨 Frontend: http://127.0.0.1:8080")

    uvicorn.run(
        "src.services.api_gateway.mock_backend:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        access_log=True,
    )
