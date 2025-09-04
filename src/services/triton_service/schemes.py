from typing import List, Tuple
from pydantic import BaseModel, Field


class EncodeIn(BaseModel):
    request_id: int = Field(..., description="Идентификатор запроса")
    text: List[str] = Field("Привет", description="Текст для кодирования")


class EncodeOut(BaseModel):
    request_id: int = Field(..., description="Идентификатор запроса")
    vectors: List[str] = Field(..., description="Эмбединг текста")


class RerankIn(BaseModel):
    request_id: int = Field(..., description="Идентификатор запроса")
    pairs: List[Tuple[str, str]] = Field(
        [("Привет", "Пока"), ("Привет", "ААА")], description="Тексты для оценки"
    )


class RerankOut(BaseModel):
    request_id: int = Field(..., description="Идентификатор запроса")
    scores: List[float] = Field(
        [0.5, 0.8], description="Скоры похожести текстов"
    )
