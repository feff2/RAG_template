from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str = None

class QueryResponse(BaseModel):
    response: str
    session_id: str

class PipelineIn(BaseModel):
    query: str
    session_id: str

class RetrievalRes(BaseModel):
    documents: List[Dict]
    scores: List[float]

class GenerateIn(BaseModel):
    session_id: str
    context: str
    query: str

class GenerateOut(BaseModel):
    sessinon_id: str
    generated: str