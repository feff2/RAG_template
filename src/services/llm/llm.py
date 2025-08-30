from typing import Dict, List

from openai import OpenAI

from src.services.llm.chat_history import ChatHistory
from src.shared import config


class VllmClient:
    def __init__(
        self,
        url: str = config.llm_server_url,
        api_key: str = config.llm_api_key,
        model: str = config.model_name,
    ) -> None:
        self.client = OpenAI(base_url=url, api_key=api_key)
        self.model = model

    def generate(self, chat_history: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=chat_history,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        answer = response.choices[0].message.content
        return answer


if __name__ == "__main__":
    chat = ChatHistory()
    chat.add_user_message("Hello, how are you?")
    vllm_client = VllmClient()
    response = vllm_client.generate(chat.history)
    print("Response:", response)
