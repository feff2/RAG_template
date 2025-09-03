import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from .schema import (
    CreateCollectionRequest,
    UpsertRequest,
    SearchRequest,
    SearchResponse,
    SearchHit,
)

from .service import VectorDbService

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Vector Index & Search Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Vector API lifespan: init VectorDbService")
    vdb = VectorDbService()
    app.state.vdb = vdb

    app.state.id_counter = int(time.time() * 1000)

    try:
        health_fn = getattr(vdb.client, "health", None)
        if health_fn:
            if asyncio.iscoroutinefunction(health_fn):
                await health_fn()
            else:
                health_fn()
    except Exception:
        logger.exception("Qdrant health-check failed on startup (ignored)")

    try:
        yield
    finally:
        logger.info("Shutting down Vector API: closing VectorDbService")
        try:
            await vdb.close()
        except Exception:
            logger.exception("Error closing VectorDbService")


app.router.lifespan_context = lifespan


async def get_vdb() -> VectorDbService:
    vdb: VectorDbService = app.state.vdb
    return vdb


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/collections/{collection_name}/create", status_code=201)
async def create_collection(
    collection_name: str = Path(..., description="Имя коллекции"),
    req: CreateCollectionRequest | None = None,
    vdb: VectorDbService = Depends(get_vdb),
):
    try:
        await vdb.create_collection(
            collection_name=collection_name,
            vector_size=req.vector_size if req else None,
            dense_vector_name=(req.dense_vector_name if req else None),
            sparse_vector_names=(req.sparse_vector_names if req else None),
            sparse_on_disk=(req.sparse_on_disk if req else False),
        )
    except Exception as e:
        logger.exception("create_collection failed")
        raise HTTPException(status_code=500, detail=str(e))
    return {"created": True, "collection": collection_name}


@app.post("/collections/{collection_name}/upsert", status_code=200)
async def upsert_points(
    collection_name: str,
    req: UpsertRequest,
    vdb: VectorDbService = Depends(get_vdb),
):
    points_dict: Dict[int, Dict[str, Any]] = {}
    generated_map: Dict[int, int] = {}

    counter = app.state.id_counter

    for idx, vec_in in enumerate(req.vectors):
        counter += 1
        gen_id = int(counter)
        # store
        points_dict[gen_id] = {"vector": vec_in.vector}
        generated_map[idx] = gen_id

    app.state.id_counter = counter

    try:
        await vdb.upsert_points(
            collection_name=collection_name, points=points_dict, wait=True
        )
    except Exception as e:
        logger.exception("upsert failed")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "upserted": len(points_dict),
        "collection": collection_name,
        "generated_ids": generated_map,
    }


@app.post("/collections/{collection_name}/search", response_model=SearchResponse)
async def hybrid_search(
    collection_name: str,
    req: SearchRequest,
    vdb: VectorDbService = Depends(get_vdb),
):
    try:
        merged_sorted = await vdb.hybrid_search(
            collection_name=collection_name,
            query_dense=req.query_dense,
            query_sparse=req.query_sparse,
            sparse_name=req.sparse_name,
            top_k=req.top_k,
            prefetch_k=req.prefetch_k,
            weight_dense=req.weight_dense,
            weight_sparse=req.weight_sparse,
            rrf_k=req.rrf_k,
            with_payload=req.with_payload,
        )
    except Exception as e:
        logger.exception("search failed")
        raise HTTPException(status_code=500, detail=str(e))

    hits = []
    for item in merged_sorted:
        hits.append(
            SearchHit(
                id=item.get("id"),
                rrf_score=float(item.get("rrf_score", 0.0)),
                payload=item.get("payload"),
                score_dense=item.get("score_dense"),
                score_sparse=item.get("score_sparse"),
            )
        )
    return SearchResponse(results=hits)
