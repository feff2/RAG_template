from typing import List

import requests

from src.shared.config import embedding_server_url


class EmbedClient:
    def __init__(self, url: str = embedding_server_url, batch_size: int = 512) -> None:
        self.url = url
        self.batch_size = batch_size

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
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


if __name__ == "__main__":
    client = EmbedClient(batch_size=512)
    texts = [f"текст {i}" for i in range(10000)]
    vectors = client.embed(texts)
    print(f"Получено {len(vectors)} эмбеддингов")
    print("Размер одного эмбеддинга:", len(vectors[0]))
