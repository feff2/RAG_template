import copy

from src.services.chat.chat_history import ChatHistory
from src.services.db.redis_chat_db import RedisChatDB
from src.services.llm.llm import VllmClient
from src.services.llm.prompts import RAG_NEED_TO_RETRIEVE, RAG_SYSTEM_PROMPT
from src.services.retrivers.pipeline import RetrievePipeline


class ChatEngine:
    def __init__(self) -> None:
        self.client = None 
        self.chat_db = None
        self.retriever = None

    def start(self):
        self.client = VllmClient()
        self.chat_db = RedisChatDB(redis_url="redis://localhost:6379/0", ttl=60*60*24) 
        self.retriever = RetrievePipeline()

    def close(self):
        self.client = None 
        self.chat_db = None
        self.retriever = None

    def user_query(self, user_id: str, message: str) -> str:
        history = self.chat_db.get_chat(user_id)

        if history.history == []:
            history.add_system_message(RAG_SYSTEM_PROMPT)

        history.add_user_message(message)

        copy_history = copy.deepcopy(history)
        if self.need_retrieve(copy_history):
            retrieved, documents = self.retriever.run(message)
            history.add_user_message(retrieved)
        
        history.truncate_history()
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

