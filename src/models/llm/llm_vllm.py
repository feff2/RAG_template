from typing import Optional, Dict, Union

import torch
from vllm import LLM, SamplingParams

from src.services.llm.llm import Llm


class LlmVLLM(Llm):
    def __init__(
        self,
        model_name: str,
        device: Union[str, torch.device] = "cuda:0",
        params: Optional[Dict] = None,
        system_prompt: str = "",
        history_max_tokens: int = 2048,
    ):
        super().__init__(
            model_name, device, params or {}, system_prompt, history_max_tokens
        )
        self.model = LLM(model=self.model_name)
        self.params: SamplingParams = SamplingParams(**params)

    def generate(
        self,
        context: str,
        query: str,
        return_full_prompt: bool = False,
    ) -> Union[str, Dict]:
        if self.client is None:
            self.load()
        prompt_text = self._build_prompt(context=context, query=query)
        inputs = self._truncate_to_fit(prompt_text, self.params.max_new_tokens)
        outputs = self.client.generate(inputs, sampling_params=self.params)

        response_text = ""
        first = None
        for item in outputs:
            first = item
            break
        if first is None:
            response_text = ""
        else:
            if (
                hasattr(first, "outputs")
                and len(first.outputs) > 0
                and hasattr(first.outputs[0], "text")
            ):
                response_text = first.outputs[0].text

            elif hasattr(first, "generated_text"):
                response_text = first.generated_text
            else:
                response_text = str(first)
        response_text = str(first)

        response_text = response_text.strip()

        self.history.append(query, response_text)

        if return_full_prompt:
            return {"response": response_text, "prompt_text": inputs}
        return response_text
