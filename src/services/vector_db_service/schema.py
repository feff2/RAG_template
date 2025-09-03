from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SparseVectorIn(BaseModel):
    indices: List[int] = Field(
        ..., description="Индексы ненулевых элементов sparse-вектора"
    )
    values: List[float] = Field(
        ..., description="Значения для соответствующих индексов"
    )


VectorType = Union[
    List[float], Dict[str, Union[List[float], SparseVectorIn, Dict[str, Any]]]
]


class VectorIn(BaseModel):
    vector: VectorType = Field(
        ..., description="Dense vector or named vector map (dense or sparse)"
    )


class UpsertRequest(BaseModel):
    vectors: List[VectorIn] = Field(
        ...,
        description="Список векторов для индексации (только вектора, без id/payload)",
    )


class CreateCollectionRequest(BaseModel):
    vector_size: Optional[int] = Field(
        None, description="Размер плотного unnamed vector (если нужен)"
    )
    dense_vector_name: Optional[str] = Field(
        None, description="Имя плотного вектора (если именованный)"
    )
    sparse_vector_names: Optional[List[str]] = Field(
        None, description="Имена sparse-vector storages"
    )
    sparse_on_disk: bool = Field(
        False, description="Использовать on-disk индекс для sparse векторов"
    )


class SearchRequest(BaseModel):
    query_dense: Optional[List[float]] = Field(
        None, description="Плотный вектор запроса"
    )
    query_sparse: Optional[Dict[int, float]] = Field(
        None, description="Словарь index->value для sparse запроса"
    )
    sparse_name: str = Field(
        "text-sparse", description="Имя sparse-vector хранилища для поиска"
    )
    top_k: int = Field(10, ge=1, description="Сколько вернуть")
    prefetch_k: int = Field(
        200, ge=1, description="Сколько извлекать из каждого источника для fusion"
    )
    weight_dense: float = Field(1.0, ge=0.0, description="Веса dense части при fusion")
    weight_sparse: float = Field(
        1.0, ge=0.0, description="Веса sparse части при fusion"
    )
    rrf_k: int = Field(60, ge=1, description="Параметр RRF")
    with_payload: bool = Field(True, description="Возвращать payload")


class SearchHit(BaseModel):
    id: Union[int, str]
    rrf_score: float
    payload: Optional[Dict[str, Any]] = None
    score_dense: Optional[float] = None
    score_sparse: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchHit]
