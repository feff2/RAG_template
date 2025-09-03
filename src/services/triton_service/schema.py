from typing import List, Tuple
from pydantic import BaseModel, Field


class EncodeIn(BaseModel):
    text: List[str] = Field("Привет", description="Текст для кодирования")


class EncodeOut(BaseModel):
    text: List[str] = Field(..., description="Эмбединг текста")


class RerankIn(BaseModel):
    pairs: List[Tuple[str, str]] = Field(
        [("Привет", "Пока")], [("Привет", "ААА")], description="Тексты для оценки"
    )


class RerankOut(BaseModel):
    scores: List[float] = Field(
        List[0.5, 0.8, 0.93884], description="Скоры похожести текстов"
    )
