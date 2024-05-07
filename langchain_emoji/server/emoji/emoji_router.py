import logging
from fastapi import APIRouter, Depends, Request
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
