from src.models.llm.llm_vllm import LlmVLLM


class LLMService:
    def __init__(
        self: "LLMService", model_name, device, params, system_prompt, history_max_token
    ):
        self.model = LlmVLLM(
            model_name=model_name,
            device=device,
            params=params,
            system_prompt=system_prompt,
            history_max_tokens=history_max_token,
        )

    async def generate(self: "LLMService", context: str, query: str):
        return self.model.generate(
            context=context,
            query=query,
        )
