import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Union, Optional
from langchain_emoji.server.utils.auth import authenticated
from langchain_emoji.server.emoji.emoji_service import (
    EmojiService,
    EmojiRequest,
    EmojiResponse,
)
from langchain_emoji.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
)
from uuid import UUID

logger = logging.getLogger(__name__)

emoji_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


@emoji_router.post(
    "/emoji",
    response_model=RestfulModel[EmojiResponse | int | None],
    tags=["Emoji"],
)
async def emoji_invoke(request: Request, body: EmojiRequest) -> RestfulModel:
    """
    Call directly to return search results
    """
    service = request.state.injector.get(EmojiService)
    try:
        return RestfulModel(data=await service.get_emoji(body))
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


class SendFeedbackBody(BaseModel):
    run_id: UUID
    key: str = "user_score"

    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None


@emoji_router.post(
    "/emoji/feedback",
    tags=["Emoji"],
)
async def send_feedback(request: Request, body: SendFeedbackBody):
    service = request.state.injector.get(EmojiService)
    service.trace_service.trace_client.create_feedback(
        body.run_id,
        body.key,
        score=body.score,
        comment=body.comment,
        feedback_id=body.feedback_id,
    )
    return RestfulModel(data="posted feedback successfully")


class GetTraceBody(BaseModel):
    run_id: UUID


@emoji_router.post(
    "/get_trace",
    tags=["Emoji"],
)
async def get_trace(request: Request, body: GetTraceBody):
    service = request.state.injector.get(EmojiService)

    run_id = body.run_id
    if run_id is None:
        return RestfulModel(
            code=SystemErrorCode, msg="No LangSmith run ID provided", data=None
        )
    return RestfulModel(data=await service.trace_service.aget_trace_url(str(run_id)))
