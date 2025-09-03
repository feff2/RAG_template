from typing import Dict

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
from .llm import Llm

class LllmVllm(Llm):
    def __init__(
            self: "LllmVllm",
            model_name: str,
            params: Dict,
        ):
        super().__init__(model_name)
        self.model = None
        self.tokenizer = None
        self.__params = SamplingParams(**params)

    def start(self: "LllmVllm") -> None:
        self.model = LLM(model=self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def close(self: "LllmVllm") -> None:
        if self.model:
            del self.model
        self.model = None
        self.tokenizer = None

    def _build_prompt(self, query: str, context: str) -> str:
        return super()._build_prompt(query, context)

    def _update_history(self, query: str, answer: str) -> None:
        return super()._update_history(query, answer)

    def _truncate_to_fit(self, text: str, max_new_tokens: int):
        return super()._truncate_to_fit(text, max_new_tokens)

    def generate(self: "LllmVllm", query: str, context: str = None) -> str:
        prompt = self._build_prompt(query, context or "")
        prompt = self._truncate_to_fit(prompt, self.__params.max_tokens)
        
        outputs = self.model.generate([prompt], self.__params)
        generated_text = outputs[0].outputs[0].text
        
        self._update_history(query, generated_text)
        return generated_text