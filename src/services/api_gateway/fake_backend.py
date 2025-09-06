"""
Fake backend для тестирования фронтенда Q&A системы.

Имитирует работу основного API Gateway с теми же эндпоинтами и схемами,
но возвращает заранее подготовленные ответы вместо реальной обработки запросов.
"""

import asyncio
import random
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class QueryIn(BaseModel):
    """
    Схема входящего запроса для обработки пользовательского вопроса.

    Attributes
    ----------
    user_id : str
        Уникальный идентификатор пользователя
    query : str
        Текст пользовательского запроса
    """

    user_id: str
    query: str


class QueryOut(BaseModel):
    """
    Схема ответа на пользовательский запрос.

    Attributes
    ----------
    user_id : str
        Идентификатор пользователя
    response : tuple[str, list[str]]
        Кортеж из основного ответа и списка источников
    """

    user_id: str
    response: tuple[str, list[str]]


class FeedbackIn(BaseModel):
    """
    Схема входящего запроса для отправки обратной связи.

    Attributes
    ----------
    user_id : str
        Уникальный идентификатор пользователя
    user_message : str
        Сообщение пользователя
    model_response : str
        Ответ модели
    rating : int
        Оценка от 1 до 5 звезд
    feedback : Optional[str]
        Необязательный текстовый отзыв
    """

    user_id: str
    user_message: str
    model_response: str
    rating: int
    feedback: Optional[str] = None


# Заготовленные ответы для имитации работы RAG системы
SAMPLE_RESPONSES: List[str] = [
    "Это интересный вопрос! На основе доступной информации могу сказать, что данная тема требует детального анализа. Рекомендую обратиться к дополнительным источникам для получения более полной картины.",
    "Согласно документации, этот процесс включает несколько этапов:\n1. Анализ входных данных\n2. Поиск релевантной информации\n3. Формирование ответа\n\nДля получения более точной информации рекомендую изучить [официальную документацию](https://example.com/docs).",
    "Ваш вопрос касается важной темы. Основные моменты:\n\n• Первый аспект связан с техническими особенностями\n• Второй момент затрагивает практические применения\n• Третий пункт описывает возможные ограничения\n\nДля углубленного изучения советую посмотреть [этот ресурс](https://example.com/resource).",
    "Отличный вопрос! Могу предложить следующее объяснение:\n\nДанный подход имеет свои преимущества и недостатки. С одной стороны, он обеспечивает высокую эффективность, с другой - требует дополнительных ресурсов.\n\nБолее подробную информацию можно найти в [специализированной литературе](https://example.com/literature).",
    "По этому вопросу есть несколько точек зрения. Современные исследования показывают, что оптимальным решением является комплексный подход, учитывающий различные факторы.\n\nРекомендую ознакомиться с [последними исследованиями](https://example.com/research) в этой области.",
]

# Хранилище активных сессий (в реальной системе это было бы в Redis)
active_sessions: Dict[str, List[Dict[str, str]]] = {}

app = FastAPI(
    title="RAG Template Fake Backend",
    description="Имитация API для тестирования фронтенда",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)

# Настройка CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик исключений.

    Parameters
    ----------
    request : Request
        HTTP запрос
    exc : Exception
        Возникшее исключение

    Returns
    -------
    JSONResponse
        Ответ с информацией об ошибке
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


@app.post("/api/v1/query", response_model=QueryOut)
async def process_query(query_data: QueryIn) -> QueryOut:
    """
    Обработка пользовательского запроса с имитацией задержки.

    Parameters
    ----------
    query_data : QueryIn
        Данные запроса пользователя

    Returns
    -------
    QueryOut
        Ответ системы на запрос

    Raises
    ------
    HTTPException
        При ошибке обработки запроса
    """
    try:
        # Имитация времени обработки запроса (1-3 секунды)
        await asyncio.sleep(random.uniform(1.0, 3.0))

        # Выбор случайного ответа из заготовленных
        response_text = random.choice(SAMPLE_RESPONSES)

        # Добавление контекстной информации к ответу
        if "документ" in query_data.query.lower() or "файл" in query_data.query.lower():
            response_text += "\n\nВаш запрос касается документооборота. Найдены релевантные материалы в базе знаний."
        elif (
            "ошибка" in query_data.query.lower()
            or "проблема" in query_data.query.lower()
        ):
            response_text += "\n\nОбнаружен вопрос о решении проблемы. Рекомендую проверить [руководство по устранению неполадок](https://example.com/troubleshooting)."

        # Имитируем источники для ответа
        sources = [
            "Документация API v1.2",
            "Руководство пользователя",
            "База знаний компании",
        ]

        return QueryOut(user_id=query_data.user_id, response=(response_text, sources))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки запроса: {str(e)}",
        )


@app.post("/api/v1/feedback")
async def submit_feedback(feedback_data: FeedbackIn) -> Dict[str, bool]:
    """
    Обработка обратной связи пользователя.

    Parameters
    ----------
    feedback_data : FeedbackIn
        Данные обратной связи пользователя

    Returns
    -------
    Dict[str, bool]
        Подтверждение успешного сохранения обратной связи

    Raises
    ------
    HTTPException
        При некорректной оценке (не от 1 до 5)
    """
    try:
        # Валидация оценки
        if not (1 <= feedback_data.rating <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rating must be between 1 and 5",
            )

        # Имитация сохранения обратной связи
        print(f"Получена обратная связь от пользователя {feedback_data.user_id}")
        print(f"Оценка: {feedback_data.rating}/5 звезд")
        print(f"Сообщение пользователя: {feedback_data.user_message[:100]}...")
        print(f"Ответ модели: {feedback_data.model_response[:100]}...")
        if feedback_data.feedback:
            print(f"Дополнительный отзыв: {feedback_data.feedback}")

        # Имитация небольшой задержки обработки
        await asyncio.sleep(0.2)

        return {"ok": True}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сохранения обратной связи: {str(e)}",
        )


@app.get("/api/v1/health")
async def health_check() -> Dict[str, str]:
    """
    Проверка состояния сервиса.

    Returns
    -------
    Dict[str, str]
        Статус сервиса
    """
    return {"status": "ok", "service": "fake_backend"}


if __name__ == "__main__":
    uvicorn.run(
        "fake_backend:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        access_log=True,
    )
