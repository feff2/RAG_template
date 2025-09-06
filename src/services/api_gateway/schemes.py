from typing import Optional

from pydantic import BaseModel


class QueryIn(BaseModel):
    user_id: str
    query: str


class QueryOut(BaseModel):
    user_id: str
    response: str


class PipelineIn(BaseModel):
    user_id: str
    query: str
    history_session: str


class PipelineOut(BaseModel):
    user_id: str
    generated: str


class FeedbackIn(BaseModel):
    user_id: str
    user_message: str
    model_response: str
    rating: int
    feedback: Optional[str]
