from datetime import datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ..container import logger
from ..schemes import FeedbackIn

router = APIRouter(tags=["feedback"], include_in_schema=False)


async def __submit_feedback(request: Request, payload: FeedbackIn) -> None:
    try:
        redis_db = request.app.state.redis_chat_db

        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": payload.user_id,
            "user_message": payload.user_message,
            "model_response": payload.model_response,
            "rating": payload.rating,
            "feedback": payload.feedback,
        }

        logger.info(
            f"Get feedback rating: {payload.rating}, message: {payload.feedback}"
        )
        await run_in_threadpool(redis_db.client.rpush, "feedbacks", str(feedback_entry))

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"detail": "Feedback saved successfully"},
        )

    except Exception as e:
        logger.exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to save feedback"},
        )


@router.post("/feedback")
async def feedback(request: Request, input_: FeedbackIn) -> None:
    return await __submit_feedback(request, input_)
