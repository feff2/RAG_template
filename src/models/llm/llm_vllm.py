import torch
from typing import Dict

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
from .llm import Llm

class LllmVllm(Llm):
    def __init__(
            self: "LllmVllm",
            model_name: str,
            device: torch.device,
            params: Dict,
            system_prompt: str,
            history_max_tokens: int,
        ):
        super().__init__(
            model_name,
            device,
            params,
            system_prompt,
            history_max_tokens
        )
        self.model = None
        self.tokenizer = None
        self._system_prompt = system_prompt
        self.__params = SamplingParams(**params)
        self._device = device

    def start(self: "LllmVllm") -> None:
        self.model = LLM(
            self.model_name, 
            skip_tokenizer_init=True,
            tensor_parallel_size=1,
            swap_space=1,
            gpu_memory_utilization=0.7,
            max_model_len=20480, 
        )
        self._history.append(
            {"role": "system", "content": self._system_prompt},
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def close(self: "LllmVllm") -> None:
        if self.model:
            del self.model
        self.model = None
        self.tokenizer = None

    def generate(self: "LllmVllm", query: str, context: str = None) -> str:
        prompt = self._build_prompt(query, context or "")
        prompt = self._truncate_to_fit(prompt, self.__params.max_tokens)
        
        outputs = self.model.generate([prompt], self.__params)
        generated_text = outputs[0].outputs[0].text
        
        self._update_history(query, generated_text)
        return generated_text