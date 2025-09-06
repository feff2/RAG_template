from pydantic import BaseModel
from typing import Optional


class QueryIn(BaseModel):
    request_id: str
    query: str

class QueryOut(BaseModel):
    request_id: str
    response: str

class PipelineIn(BaseModel):
    request_id: str
    query: str
    history_session: str

class PipelineOut(BaseModel):
    request_id: str
    generated: str

class RatingIn(BaseModel):
    request_id: str
    history_session: str
    rating: int  
    comment: Optional[str] = None

class FeedbackIn(BaseModel):
    request_id: str
    history_session: str
    feedback: str


