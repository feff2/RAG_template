from pydantic import BaseModel, Field


class QueryIn(BaseModel):
    request_id: str = Field(1, description="Номер запроса")
    query: str = Field(..., description="Запрос от пользователя")


class QueryOut(BaseModel):
    request_id: str = Field(1, description="Номер запроса")
    answer: str = Field(..., description="Ответ на запрос")
    documents: list[dict[int, str]] = Field(..., description="Список релевантных документов")