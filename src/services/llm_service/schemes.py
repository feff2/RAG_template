from pydantic import BaseModel
from typing import Optional, Dict, Any


class GenerateIn(BaseModel):
    request_id: int
    context: str = None
    prompt: str
    system_prompt: str = None
    max_new_tokens: Optional[int] = None
    params: Optional[Dict] = None


class GenerateOut(BaseModel):
    request_id: int
    response: str

class HealthIn(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str

class ModelInfoOut(BaseModel):
    name: str
    type: str
    loaded: bool
    device: str
    parameters: Dict[str, Any]
   

