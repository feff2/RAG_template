from pydantic import BaseModel


class QueryIn(BaseModel):
    request_id: str
    query: str


class QueryOut(BaseModel):
    request_id: str
    response: tuple[str, list[str]]


class PipelineIn(BaseModel):
    request_id: str
    query: str
    history_session: str


class PipelineOut(BaseModel):
    request_id: str
    response: tuple[str, list[str]]


class FeedbackIn(BaseModel):
    request_id: str
    history_session: str
    feedback: str
