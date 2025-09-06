from typing import Dict, List

import requests
from haystack import Document, component
from tqdm import tqdm

from src.shared.config import embedding_server_url


class EmbedClient:
    def __init__(self, url: str = embedding_server_url, batch_size: int = 16) -> None:
        self.url = url
        self.batch_size = batch_size

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for i in tqdm(range(0, len(texts), self.batch_size)):
            batch = texts[i : i + self.batch_size]
            response = requests.post(
                self.url,
                json={"texts": batch},
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            embeddings.extend(data["embeddings"])
        return embeddings


@component
class DocEmbedder:
    def __init__(self, embed_client: EmbedClient) -> None:
        self.embed_client = embed_client

    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        texts = [doc.content for doc in documents]
        embeddings = self.embed_client.embed(texts)
        for doc, emb in zip(documents, embeddings):
            doc.embedding = emb
        return {"documents": documents}


@component
class QueryEmbedder:
    def __init__(self, embed_client: EmbedClient) -> None:
        self.embed_client = embed_client

    @component.output_types(embedding=List[float])
    def run(self, query: str) -> Dict[str, List[float]]:
        print(f"Generating embedding for query: {query}")
        embedding = self.embed_client.embed([query])[0]
        return {"embedding": embedding}


if __name__ == "__main__":
    client = EmbedClient(batch_size=512)
    texts = [f"текст {i}" for i in range(10000)]
    vectors = client.embed(texts)
    print(f"Получено {len(vectors)} эмбеддингов")
    print("Размер одного эмбеддинга:", len(vectors[0]))
