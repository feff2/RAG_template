from pydantic import BaseModel


class QueryIn(BaseModel):
    request_id: str = None
    query: str

class QueryResponse(BaseModel):
    request_id: str
    response: str

class PipelineIn(BaseModel):
    request_id: str
    query: str
    history_session: str
class PipelineOut(BaseModel):
    request_id: str
    generated: str