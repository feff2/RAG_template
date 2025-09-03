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

    def load(self) -> AutoModelForCausalLM:
        torch_dtype = None
        if self.params.get("use_fp16", False) and "cuda" in str(self.device).lower():
            torch_dtype = torch.float16

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=self.params.get("low_cpu_mem_usage", False),
        )

        if getattr(self.model, "resize_token_embeddings", None) is not None:
            self.model.resize_token_embeddings(len(self.tokenizer))

        self.model = self.model.to(self.device)
        self.model.eval()
        return self.model

    def generate(
        self, context: str, query: str, return_full_prompt: bool = False
    ) -> Union[str, Dict[str, str]]:
        if self.model is None:
            self.load()

        prompt_text = self._build_prompt(query=query, context=context or "")
        inputs = self._truncate_to_fit(prompt_text, self.params["max_new_tokens"])

        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs.get("attention_mask", None)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids, attention_mask=attention_mask, **self.params
            )

        out_ids = outputs[0][input_ids.shape[1] :]
        response = self.tokenizer.decode(out_ids, skip_special_tokens=True).strip()

        self._update_history(query, response)

        if return_full_prompt:
            return {"response": response, "prompt_text": prompt_text}
        return response
