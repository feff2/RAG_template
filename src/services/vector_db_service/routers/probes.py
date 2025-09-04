import httpx
from fastapi import APIRouter

from ..container import settings

router = APIRouter(tags=["probes"], include_in_schema=False)


@router.get("/probes/readiness/")
async def readiness() -> str:
    async with httpx.AsyncClient() as client:
        predict_result = await client.get(
            f"http://{settings.DB_HOST}:{settings.DB_PORT}/ready",
        )

        predict_result.raise_for_status()

        predict_result = await client.get(
            f"http://{settings.DB_HOST}:{settings.DB_PORT}/ready",
        )

        predict_result.raise_for_status()

        return predict_result.text


@router.get("/probes/liveness/")
async def liveness() -> str:
    async with httpx.AsyncClient() as client:
        predict_result = await client.get(
            f"http://{settings.DB_HOST}:{settings.DB_PORT}/v2/health/ready",
        )

        predict_result.raise_for_status()

        return predict_result.text