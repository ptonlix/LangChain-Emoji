import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Union, Optional
from langchain_emoji.server.utils.auth import authenticated
from langchain_emoji.server.emoji.emoji_service import (
    EmojiService,
)
from langchain_emoji.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
)
from uuid import UUID

logger = logging.getLogger(__name__)

trace_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


class SendFeedbackBody(BaseModel):
    run_id: UUID
    key: str = "user_score"

    score: Union[float, int, bool, None] = None
    feedback_id: Optional[UUID] = None
    comment: Optional[str] = None


@trace_router.post(
    "/feedback",
    tags=["Trace"],
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


@trace_router.post(
    "/get_trace",
    tags=["Trace"],
)
async def get_trace(request: Request, body: GetTraceBody):
    service = request.state.injector.get(EmojiService)

    run_id = body.run_id
    if run_id is None:
        return RestfulModel(
            code=SystemErrorCode, msg="No LangSmith run ID provided", data=None
        )
    return RestfulModel(data=await service.trace_service.aget_trace_url(str(run_id)))
