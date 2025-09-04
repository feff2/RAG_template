import httpx
from fastapi import APIRouter

from ..container import settings

router = APIRouter(tags=["probes"], include_in_schema=False)



@router.get("/probes/readiness/")
async def readiness_cross_encoder() -> str:
    async with httpx.AsyncClient() as client:
        predict_result = await client.get(
            f"http://{settings.INFERENCE_HOST_CROSS_ENCODER}:{settings.INFERENCE_PORT_CROSS_ENCODER}/ready",
        )

        predict_result.raise_for_status()

        predict_result = await client.get(
            f"http://{settings.INFERENCE_HOST_CROSS_ENCODER}:{settings.INFERENCE_PORT_CROSS_ENCODER}/ready",
        )

        predict_result.raise_for_status()

        return predict_result.text


@router.get("/probes/liveness/")
async def liveness_cross_encoder() -> str:
    async with httpx.AsyncClient() as client:
        predict_result = await client.get(
            f"http://{settings.INFERENCE_HOST_CROSS_ENCODER}:{settings.INFERENCE_PORT_CROSS_ENCODER}/v2/health/ready",
        )

        predict_result.raise_for_status()

        return predict_result.text


@router.get("/probes/readiness/")
async def readiness_bi_encoder() -> str:
    async with httpx.AsyncClient() as client:
        predict_result = await client.get(
            f"http://{settings.INFERENCE_HOST_BI_ENCODER}:{settings.INFERENCE_PORT_BI_ENCODER}/ready",
        )

        predict_result.raise_for_status()

        predict_result = await client.get(
            f"http://{settings.INFERENCE_HOST_BI_ENCODER}:{settings.INFERENCE_PORT_BI_ENCODER}/ready",
        )

        predict_result.raise_for_status()

        return predict_result.text


@router.get("/probes/liveness/")
async def liveness_bi_encoder() -> str:
    async with httpx.AsyncClient() as client:
        predict_result = await client.get(
            f"http://{settings.INFERENCE_HOST_BI_ENCODER}:{settings.INFERENCE_PORT_BI_ENCODER}/v2/health/ready",
        )

        predict_result.raise_for_status()

        return predict_result.text