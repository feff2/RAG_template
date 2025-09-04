from fastapi import APIRouter


from ..schemes import GenerateIn, GenerateOut
from ..container import llm_service, logger

router = APIRouter(tags=["generate", "llm"], include_in_schema=False)

async def __generate(
    input_: GenerateIn,
) -> GenerateOut:
    msg = f"Generate request_id={input_.request_id}, context={input_.context[:100]}"
    logger.debug(msg)

    generated = await llm_service.generate(
        input_.request_id,
        input_.context,
        input_.prompt,
        input_.system_prompt,
        input_.max_new_tokens,
        input_.params,
    )

    msg = f"Requested reques_id={generated}"
    logger.debug(msg)

    return GenerateOut(
        request_id=input_.request_id,
        response=generated,
    )

@router.post(
    f"/generate/",
    summary="Получить ответ",
)
async def predict(input_: GenerateIn) -> GenerateOut:
    return await __generate(input_)
