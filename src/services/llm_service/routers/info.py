from fastapi import APIRouter


from ..schema import ModelInfoOut
from ..main import logger, llm_service, settings

router = APIRouter(tags=["info", "llm"], include_in_schema=False)

async def __get_info(
) -> ModelInfoOut:
    msg = f"Get model info"
    logger.debug(msg)
    return ModelInfoOut(
        name=llm_service.model_name,
        type=settings.MODEL_TYPE,
        loaded=llm_service.started,
        device=settings.DEVICE.type,
        parameters=settings.PARAMS,
    )

@router.post(
    f"/info/",
    summary="Получить информацию о модели",
)
async def predict() -> ModelInfoOut:
    return await __get_info()
