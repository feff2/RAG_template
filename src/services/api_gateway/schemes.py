from typing import Optional

from pydantic import BaseModel


class QueryIn(BaseModel):
    user_id: str
    query: str
    target: Optional[str] = None


class QueryOut(BaseModel):
    user_id: str
    response: tuple[str, list[str]]


class PipelineIn(BaseModel):
    user_id: str
    query: str
    history_session: str
    target: Optional[str] = None


class PipelineOut(BaseModel):
    user_id: str
    response: tuple[str, list[str]]


class FeedbackIn(BaseModel):
    user_id: str
    user_message: str
    model_response: str
    rating: int
    feedback: Optional[str]
