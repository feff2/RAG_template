from typing import List

from src.services.retrivers.embedder import EmbedClient
from src.shared import config


class Retriever:
    def __init__(
        self, embed_client: EmbedClient, dim: int = config.embedding_model_dim
    ) -> None:
        """
        embed_client: клиент для получения эмбеддингов (например, EmbedClient)
        dim: размерность эмбеддинга используемой модели
        """
        # TODO: инициализировать faiss индекс

    def run(self, query: str, top_k: int = config.top_k) -> str:
        # TODO: реализовать поиск в faiss индексе и вернуть top_k наиболее релевантных документов в виде строки
        return ""

    def add_documents(self, documents: List[str]) -> None:
        raise NotImplementedError
