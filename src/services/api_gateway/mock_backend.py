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


class QuestionItem(BaseModel):
    normalized: str
    count: int
    examples: Optional[list[str]] = None


class QuestionsOut(BaseModel):
    generated_at: str
    limit: int
    results: list[QuestionItem]


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


@app.get("/api/v1/common_questions", response_model=QuestionsOut)
async def get_common_questions(limit: int = 10) -> QuestionsOut:
    """
    Mock эндпоинт для получения популярных вопросов

    Args:
        limit: Количество вопросов для возврата

    Returns:
        QuestionsOut: Список популярных вопросов с примерами
    """
    print(f"📊 Запрос популярных вопросов (лимит: {limit})")

    # Mock данные популярных вопросов
    mock_questions = [
        QuestionItem(
            normalized="Как подать заявку на участие в электронном аукционе?",
            count=156,
            examples=[
                "Подскажите процедуру подачи заявки на аукцион",
                "Где подать документы для участия в торгах?",
                "Как зарегистрироваться на электронный аукцион?",
                "Процедура подачи заявки на участие в закупке",
                "Как стать участником электронного аукциона?",
            ],
        ),
        QuestionItem(
            normalized="Какие документы нужны для участия в закупках?",
            count=134,
            examples=[
                "Список документов для участия в тендере",
                "Какие справки нужны для закупок?",
                "Документооборот при участии в торгах",
                "Требования к документам участника",
                "Перечень необходимых документов для аукциона",
            ],
        ),
        QuestionItem(
            normalized="Как работает система электронных закупок?",
            count=98,
            examples=[
                "Принцип работы электронных торгов",
                "Как функционирует система закупок?",
                "Объясните механизм электронных аукционов",
                "Как проходят торги в электронном виде?",
            ],
        ),
        QuestionItem(
            normalized="Требования к участникам закупок по 44-ФЗ",
            count=87,
            examples=[
                "Кто может участвовать в госзакупках?",
                "Требования 44-ФЗ к поставщикам",
                "Критерии отбора участников торгов",
                "Ограничения для участия в госзакупках",
            ],
        ),
        QuestionItem(
            normalized="Как обжаловать результаты торгов?",
            count=76,
            examples=[
                "Процедура обжалования итогов аукциона",
                "Куда подавать жалобу на результаты торгов?",
                "Как опротестовать решение заказчика?",
                "Порядок обжалования в ФАС",
            ],
        ),
        QuestionItem(
            normalized="Электронная подпись для участия в закупках",
            count=65,
            examples=[
                "Как получить ЭЦП для торгов?",
                "Требования к электронной подписи",
                "Где оформить сертификат ЭП?",
                "Какая подпись нужна для аукционов?",
            ],
        ),
        QuestionItem(
            normalized="Банковская гарантия в закупках",
            count=54,
            examples=[
                "Как оформить банковскую гарантию?",
                "Требования к банковским гарантиям",
                "Где получить гарантию для торгов?",
            ],
        ),
        QuestionItem(
            normalized="Малый и средний бизнес в закупках",
            count=43,
            examples=[
                "Льготы для МСП в закупках",
                "Как участвовать МСП в торгах?",
                "Преференции для малого бизнеса",
            ],
        ),
        QuestionItem(
            normalized="Контракт после победы в торгах",
            count=32,
            examples=[
                "Как заключается контракт после аукциона?",
                "Сроки подписания договора",
            ],
        ),
        QuestionItem(
            normalized="Антидемпинговые меры в закупках",
            count=21,
            examples=["Что такое антидемпинг в торгах?"],
        ),
        QuestionItem(normalized="Единственный поставщик", count=1, examples=[]),
    ]

    # Ограничиваем количество вопросов
    if limit == 200:
        actual_limit = len(mock_questions)
    else:
        actual_limit = min(limit, len(mock_questions))
    selected_questions = mock_questions[:actual_limit]

    return QuestionsOut(
        generated_at="2024-01-15T10:30:00Z",
        limit=actual_limit,
        results=selected_questions,
    )


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
