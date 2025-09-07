import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from src.services.retrivers.embedder import EmbedClient
from src.shared.logger import CustomLogger

DEFAULT_COLLECTION = "chat_messages"
DEFAULT_DISTANCE = qm.Distance.COSINE
DEFAULT_BATCH = 64


class QdrantChatDB:
    def __init__(
        self,
        vector_size: int,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection: str = DEFAULT_COLLECTION,
        distance: qm.Distance = DEFAULT_DISTANCE,
        embed_client: Optional[EmbedClient] = None,
        recreate: bool = False,
    ) -> None:
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection = collection
        self.vector_size = vector_size
        self.distance = distance
        self.embed_client = EmbedClient()
        self.logger = CustomLogger("qdrant_chat_db")

        if recreate:
            try:
                self.client.recreate_collection(
                    collection_name=self.collection,
                    vectors_config=qm.VectorParams(
                        size=self.vector_size, distance=self.distance
                    ),
                )
            except Exception:
                self.ensure_collection()
        else:
            self.ensure_collection()

    def ensure_collection(self) -> None:
        try:
            collections = [c.name for c in self.client.get_collections().collections]
        except Exception:
            collections = []
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(
                    size=self.vector_size, distance=self.distance
                ),
            )

    @staticmethod
    def _ts() -> float:
        return time.time()

    def upsert_message(
        self,
        chat_id: str,
        text: str,
        role: str = "user",
        vector: Optional[List[float]] = None,
        normalized: Optional[str] = None,
        timestamp: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        ts = timestamp if timestamp is not None else self._ts()

        if vector is None:
            if self.embed_client is None:
                raise RuntimeError("No vector provided and no embed_client configured")
            vector = self.embed_client.embed(text)

        payload = {
            "chat_id": chat_id,
            "role": role,
            "text": text,
            "normalized": normalized,
            "timestamp": ts,
        }
        if meta:
            payload["meta"] = meta

        point = qm.PointStruct(vector=vector, payload=payload)
        self.client.upsert(collection_name=self.collection, points=[point])

    def upsert_messages(self, q_items: list[dict]) -> None:
        buffer = []
        for idx, item in enumerate(q_items):
            if item["role"]:
                payload = {
                    "chat_id": item["chat_id"],
                    "text": item["text"],
                    "role": item["role"],
                    "normalized": item.get("normalized"),
                    "timestamp": item["timestamp"],
                    "meta": item.get("meta", {}),
                }

                point_id = item.get("point_id") or idx

                vec = self.embed_client.embed([item["text"]])
                buffer.append(
                    qm.PointStruct(
                        id=point_id,
                        vector=vec[0]
                        if isinstance(vec, list) and isinstance(vec[0], list)
                        else vec,
                        payload=payload,
                    )
                )

            if buffer:
                self.client.upsert(collection_name=self.collection, points=buffer)

    def search_similar(
        self,
        query: str,
        top_k: int = 10,
        with_payload: bool = True,
    ) -> List[Dict[str, Any]]:
        if self.embed_client is None:
            raise RuntimeError("embed_client required for semantic search")

        vec = self.embed_client.embed([query])[0]

        hits = self.client.search(
            collection_name=self.collection,
            query_vector=vec,
            limit=top_k,
            with_payload=with_payload,
        )

        return [
            {"id": h.id, "score": h.score, "payload": (h.payload or {})} for h in hits
        ]

    def top_normalized_themes(
        self, limit: int = 50, since_ts: float | None = None
    ) -> List[Tuple[str, int]]:
        flt = None
        if since_ts is not None:
            flt = qm.Filter(
                must=[qm.FieldCondition(key="timestamp", range=qm.Range(gte=since_ts))]
            )

        counter = Counter()
        offset = None
        batch = 500
        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=flt,
                with_payload=True,
                limit=batch,
                offset=offset,
            )
            if not points:
                break
            for p in points:
                payload = p.payload or {}
                norm_theme = payload.get("normalized_theme")
                if norm_theme:
                    counter[norm_theme] += 1
            if next_offset is None:
                break
            offset = next_offset
        return counter.most_common(limit)

    def get_messages_by_chat(
        self, chat_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        flt = qm.Filter(
            must=[qm.FieldCondition(key="chat_id", match=qm.MatchValue(value=chat_id))]
        )
        res: List[Dict[str, Any]] = []

        scroll = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=flt,
            with_payload=True,
            limit=limit,
        )
        points, _ = scroll
        for p in points:
            res.append({"id": p.id, "payload": p.payload or {}})

        return sorted(res, key=lambda x: x["payload"].get("timestamp", 0), reverse=True)

    def top_normalized_phrases(
        self, limit: int = 50, since_ts: Optional[float] = None
    ) -> List[Tuple[str, int]]:
        flt = None
        if since_ts is not None:
            flt = qm.Filter(
                must=[qm.FieldCondition(key="timestamp", range=qm.Range(gte=since_ts))]
            )

        counter = Counter()
        offset = None
        batch = 500
        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=flt,
                with_payload=True,
                limit=batch,
                offset=offset,
            )
            if not points:
                break
            for p in points:
                payload = p.payload or {}
                norm = payload.get("normalized")
                if norm:
                    counter[norm] += 1
            if next_offset is None:
                break
            offset = next_offset
        return counter.most_common(limit)

    def delete_chat(self, chat_id: str) -> None:
        flt = qm.Filter(
            must=[qm.FieldCondition(key="chat_id", match=qm.MatchValue(value=chat_id))]
        )
        self.client.delete(collection_name=self.collection, points_selector=flt)

    def update_response_quality(self, point_id: str, quality: float) -> None:
        self.client.set_payload(
            collection_name=self.collection,
            payload={"response_quality": quality},
            points_selector=qm.PointIdsList(points=[point_id]),
        )

    def scroll_points(
        self,
        limit: int = 10000,
        offset: Optional[str] = None,
        filter: Optional[qm.Filter] = None,
    ) -> List[Dict[str, Any]]:
        points, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=filter,
            with_payload=True,
            limit=limit,
            offset=offset,
        )
        return [
            {"id": p.id, "payload": p.payload or {}, "vector": p.vector} for p in points
        ]

    def close(self) -> None:
        try:
            if hasattr(self.client, "close"):
                self.client.close()
        except Exception:
            pass
