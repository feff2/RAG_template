import os
import time
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from src.services.retrivers.embedder import EmbedClient

DEFAULT_COLLECTION = "chat_messages"
DEFAULT_VECTOR_SIZE = 1536
DEFAULT_DISTANCE = qm.Distance.COSINE
DEFAULT_BATCH = 64


load_dotenv()

server_ip = os.getenv("EMBEDDING_SERVER_IP", "localhost")


class QdrantChatDB:
    def __init__(
        self,
        url: str = f"http://{server_ip}:6333",
        api_key: Optional[str] = None,
        collection: str = DEFAULT_COLLECTION,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        distance: qm.Distance = DEFAULT_DISTANCE,
        embed_client: Optional[EmbedClient] = None,
        recreate: bool = False,
    ) -> None:
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection = collection
        self.vector_size = vector_size
        self.distance = distance
        self.embed_client = embed_client
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

    @staticmethod
    def _make_point_id(chat_id: str, ts: float, uniq: Optional[int] = None) -> str:
        base = f"{chat_id}:{int(ts * 1000)}"
        if uniq is not None:
            return f"{base}:{uniq}"
        return base

    def upsert_message(
        self,
        chat_id: str,
        text: str,
        role: str = "user",
        point_id: Optional[str] = None,
        vector: Optional[List[float]] = None,
        normalized: Optional[str] = None,
        timestamp: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        ts = timestamp if timestamp is not None else self._ts()
        if point_id is None:
            point_id = self._make_point_id(chat_id, ts)

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

        point = qm.PointStruct(id=point_id, vector=vector, payload=payload)
        self.client.upsert(collection_name=self.collection, points=[point])
        return point_id

    def upsert_messages(
        self,
        items: Iterable[Dict[str, Any]],
        batch_size: int = DEFAULT_BATCH,
    ) -> None:
        buffer: List[qm.PointStruct] = []
        for it in items:
            chat_id = it["chat_id"]
            text = it["text"]
            role = it.get("role", "user")
            ts = it.get("timestamp", self._ts())
            pid = it.get("point_id", self._make_point_id(chat_id, ts))
            vec = it.get("vector")
            if vec is None:
                if self.embed_client is None:
                    raise RuntimeError(
                        "EmbedClient required for vectorizing messages in batch"
                    )
                vec = self.embed_client.embed(text)
            payload = {
                "chat_id": chat_id,
                "role": role,
                "text": text,
                "normalized": it.get("normalized"),
                "timestamp": ts,
            }
            if it.get("meta"):
                payload["meta"] = it["meta"]
            buffer.append(qm.PointStruct(id=pid, vector=vec, payload=payload))

            if len(buffer) >= batch_size:
                self.client.upsert(collection_name=self.collection, points=buffer)
                buffer = []

        if buffer:
            self.client.upsert(collection_name=self.collection, points=buffer)

    def search_similar(
        self,
        query: str,
        top_k: int = 10,
        with_payload: bool = True,
        with_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        if self.embed_client is None:
            raise RuntimeError("embed_client required for semantic search")
        vec = self.embed_client.embed(query)
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=vec,
            limit=top_k,
            with_payload=with_payload,
            with_vector=with_vector,
        )
        out = []
        for h in hits:
            out.append({"id": h.id, "score": h.score, "payload": (h.payload or {})})
        return out

    def get_messages_by_chat(
        self, chat_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        flt = qm.Filter(
            must=[qm.FieldCondition(key="chat_id", match=qm.MatchValue(value=chat_id))]
        )
        points = self.client.scroll(
            collection_name=self.collection,
            filter=flt,
            with_payload=True,
            with_vector=False,
            limit=limit,
        )
        res = []
        for p in points:
            payload = p.payload or {}
            res.append({"id": p.id, "payload": payload})
        res_sorted = sorted(
            res, key=lambda x: x["payload"].get("timestamp", 0), reverse=True
        )
        return res_sorted[:limit]

    def top_normalized_phrases(
        self, limit: int = 50, since_ts: Optional[float] = None
    ) -> List[Tuple[str, int]]:
        flt = None
        if since_ts is not None:
            flt = qm.Filter(
                must=[qm.FieldCondition(key="timestamp", range=qm.Range(gte=since_ts))]
            )

        counter = Counter()
        offset = 0
        batch = 500
        while True:
            pts = self.client.scroll(
                collection_name=self.collection,
                with_payload=True,
                with_vector=False,
                limit=batch,
                offset=offset,
                filter=flt,
            )
            if not pts:
                break
            for p in pts:
                payload = p.payload or {}
                norm = payload.get("normalized")
                if norm:
                    counter[norm] += 1
            offset += len(pts)
            if len(pts) < batch:
                break
        return counter.most_common(limit)

    def delete_chat(self, chat_id: str) -> None:
        flt = qm.Filter(
            must=[qm.FieldCondition(key="chat_id", match=qm.MatchValue(value=chat_id))]
        )
        self.client.delete(collection_name=self.collection, filter=flt)

    def update_response_quality(self, point_id: str, quality: float) -> None:
        self.client.set_payload(
            collection_name=self.collection,
            payload={"response_quality": quality},
            points_selector=qm.PointIdsList(points=[point_id]),
        )

    def scroll_points(
        self, limit: int = 10000, offset: int = 0, filter: Optional[qm.Filter] = None
    ) -> List[Dict[str, Any]]:
        pts = self.client.scroll(
            collection_name=self.collection,
            with_payload=True,
            with_vector=True,
            limit=limit,
            offset=offset,
            filter=filter,
        )
        out = []
        for p in pts:
            out.append({"id": p.id, "payload": p.payload or {}, "vector": p.vector})
        return out

    def close(self) -> None:
        try:
            if hasattr(self.client, "close"):
                self.client.close()
        except Exception:
            pass
