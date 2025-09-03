import asyncio
from typing import Any, Dict, List, Optional
from collections import defaultdict

from qdrant_client import AsyncQdrantClient


from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVectorParams,
    SparseIndexParams,
    SparseVector,
    NamedSparseVector,
)

from .settings import Settings

from src.shared.logger import CustomLogger


class VectorDbService:
    def __init__(self, url: Optional[str] = None) -> None:
        self.settings = Settings()
        self.url = url or getattr(self.settings, "url", None)
        self.logger = CustomLogger("VectorDbService")
        self.client = AsyncQdrantClient(url=self.url)

    async def __aenter__(self) -> "VectorDbService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        try:
            close_fn = getattr(self.client, "close", None)
            if asyncio.iscoroutinefunction(close_fn):
                await close_fn()
            elif callable(close_fn):
                close_fn()
            else:
                aclose_fn = getattr(self.client, "aclose", None)
                if aclose_fn is not None:
                    await aclose_fn()
        except Exception:
            self.logger.exception("Error while closing Qdrant client, ignoring.")

    async def create_collection(
        self,
        collection_name: str,
        vector_size: Optional[int] = None,
        dense_vector_name: Optional[str] = None,
        sparse_vector_names: Optional[List[str]] = None,
        sparse_on_disk: bool = False,
    ) -> None:
        vectors_config = {}
        if vector_size is not None:
            if dense_vector_name:
                vectors_config[dense_vector_name] = VectorParams(
                    size=vector_size, distance=Distance.Cosine
                )
            else:
                vectors_config = VectorParams(
                    size=vector_size, distance=Distance.Cosine
                )

        sparse_vectors_config = None
        if sparse_vector_names:
            sparse_vectors_config = {
                name: SparseVectorParams(
                    index=SparseIndexParams(on_disk=sparse_on_disk)
                )
                for name in sparse_vector_names
            }

        try:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
            )
            self.logger.info(
                "Created collection '%s' (dense=%s, sparse=%s)",
                collection_name,
                bool(vector_size),
                sparse_vector_names,
            )
        except Exception:
            self.logger.exception("Failed to create collection '%s'", collection_name)
            raise

    async def upsert_points(
        self,
        collection_name: str,
        points: Dict[int, Dict[str, Any]],
        wait: bool = True,
    ) -> None:
        point_structs: List[PointStruct] = []
        for pid, entry in points.items():
            if "vector" not in entry:
                raise ValueError(f"Point {pid} has no 'vector' key")
            vector = entry["vector"]
            payload = entry.get("payload")

            if isinstance(vector, list):
                vs = vector
            elif isinstance(vector, dict):
                vs = {}
                for name, vect_val in vector.items():
                    if (
                        isinstance(vect_val, dict)
                        and "indices" in vect_val
                        and "values" in vect_val
                    ):
                        vs[name] = SparseVector(
                            indices=list(vect_val["indices"]),
                            values=list(vect_val["values"]),
                        )
                    else:
                        vs[name] = list(vect_val)
            else:
                raise TypeError(
                    f"Unsupported vector type for point {pid}: {type(vector)}"
                )

            point_structs.append(PointStruct(id=pid, vector=vs, payload=payload))

        try:
            await self.client.upsert(
                collection_name=collection_name, points=point_structs, wait=wait
            )
            self.logger.info(
                "Upserted %d points into '%s'", len(point_structs), collection_name
            )
        except Exception:
            self.logger.exception("Failed to upsert points into '%s'", collection_name)
            raise

    async def hybrid_search(
        self,
        collection_name: str,
        query_dense: Optional[List[float]] = None,
        query_sparse: Optional[Dict[int, float]] = None,
        sparse_name: str = "text-sparse",
        top_k: int = 10,
        prefetch_k: int = 200,
        weight_dense: float = 1.0,
        weight_sparse: float = 1.0,
        rrf_k: int = 60,
        with_payload: bool = True,
    ) -> List[Dict[str, Any]]:
        results_by_id: Dict[int, float] = defaultdict(float)
        details_by_id: Dict[int, Dict[str, Any]] = {}

        if query_dense is not None:
            dense_hits = await self.client.search(
                collection_name=collection_name,
                query_vector=query_dense,
                limit=prefetch_k,
                with_payload=with_payload,
                with_vectors=False,
            )
            for rank, hit in enumerate(dense_hits):
                pid = int(hit.id)
                rrf_score = weight_dense * (1.0 / (rrf_k + rank + 1))
                results_by_id[pid] += rrf_score
                if pid not in details_by_id:
                    details_by_id[pid] = {
                        "id": pid,
                        "score_dense": float(getattr(hit, "score", 0.0) or 0.0),
                        "payload": hit.payload,
                    }

        if query_sparse is not None:
            named_sparse = NamedSparseVector(
                name=sparse_name,
                vector=SparseVector(
                    indices=list(query_sparse.keys()),
                    values=list(query_sparse.values()),
                ),
            )
            sparse_hits = await self.client.search(
                collection_name=collection_name,
                query_vector=named_sparse,
                limit=prefetch_k,
                with_payload=with_payload,
                with_vectors=False,
            )
            for rank, hit in enumerate(sparse_hits):
                pid = int(hit.id)
                rrf_score = weight_sparse * (1.0 / (rrf_k + rank + 1))
                results_by_id[pid] += rrf_score
                if pid not in details_by_id:
                    details_by_id[pid] = {
                        "id": pid,
                        "score_sparse": float(getattr(hit, "score", 0.0) or 0.0),
                        "payload": hit.payload,
                    }
                else:
                    details_by_id[pid].setdefault(
                        "score_sparse", float(getattr(hit, "score", 0.0) or 0.0)
                    )

        merged = [
            {
                "id": pid,
                "rrf_score": score,
                **details_by_id.get(pid, {}),
            }
            for pid, score in results_by_id.items()
        ]
        merged_sorted = sorted(merged, key=lambda x: x["rrf_score"], reverse=True)[
            :top_k
        ]
        return merged_sorted
