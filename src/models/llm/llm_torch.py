import torch
from transformers import AutoModelForCausalLM
from typing import Optional, Dict, Union

from src.services.llm.llm import Llm


class LlmTorch(Llm):
    def __init__(
        self,
        model_name: str,
        device: Union[str, torch.device],
        params: Optional[Dict] = None,
        system_prompt: str = "",
        history_max_tokens: int = 2048,
    ):
        super().__init__(
            model_name, device, params or {}, system_prompt, history_max_tokens
        )
        self.model: Optional[AutoModelForCausalLM] = None

    def start(self) -> AutoModelForCausalLM:
        pass

    def generate(
        self, context: str, query: str, return_full_prompt: bool = False
    ) -> Union[str, Dict[str, str]]:
        pass
