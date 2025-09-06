import copy

from src.services.chat.chat_history import ChatHistory
from src.services.db.chat_db import ChatDB
from src.services.llm.llm import VllmClient
from src.services.llm.prompts import RAG_NEED_TO_RETRIEVE, RAG_SYSTEM_PROMPT
from src.services.retrivers.pipeline import RetrievePipeline


class ChatEngine:
    def __init__(self) -> None:
        self.client = VllmClient()
        self.chat_db = ChatDB()
        self.retriever = RetrievePipeline()

    def user_query(self, user_id: str, message: str) -> str:
        history = self.chat_db.get_chat(user_id)

        if history.history == []:
            history.add_system_message(RAG_SYSTEM_PROMPT)

        history.add_user_message(message)

        copy_history = copy.deepcopy(history)
        if self.need_retrieve(copy_history):
            retrieved, _ = self.retriever.run(message)
            print(retrieved)
            history.add_user_message(retrieved)

        answer = self.client.generate(history.history)
        history.add_assistant_message(answer)
        self.chat_db.save_chat(user_id, history)
        return answer

    def need_retrieve(self, messages: ChatHistory) -> bool:
        messages.add_system_message(RAG_NEED_TO_RETRIEVE)
        response = self.client.generate(messages.history)
        sub_string = "да"
        if sub_string in response.lower():
            return True
        return False


if __name__ == "__main__":
    engine = ChatEngine()
    user_id = "test3"
    while True:
        user_input = input("User: ")
        model_out = engine.user_query(user_id, user_input)
        print("Assistant:", model_out)
