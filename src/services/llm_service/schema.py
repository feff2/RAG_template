from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any


class GenerateRequest(BaseModel):
    context: Optional[Union[str, List[str]]] = None
    prompt: str
    system_prompt: Optional[str] = None
    max_new_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    do_sample: Optional[bool] = None
    return_full_prompt: bool = False


class GenerateResponse(BaseModel):
    response: str
    prompt_text: Optional[str] = None
    model_name: str
    generation_params: Dict[str, Any]


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
    max_new_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    do_sample: Optional[bool] = None


class ChatResponse(BaseModel):
    response: str
    model_name: str
    generation_params: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str


class ModelInfo(BaseModel):
    name: str
    type: str
    loaded: bool
    device: str
    parameters: Dict[str, Any]


class ClearHistoryRequest(BaseModel):
    session_id: Optional[str] = None


class ClearHistoryResponse(BaseModel):
    status: str
    message: str
