import logging
from fastapi import APIRouter, Depends, Request
from typing import Any, List
from pydantic import BaseModel, Field
from langchain_emoji.server.utils.auth import authenticated
from langchain_emoji.server.vector_store.vector_store_server import (
    VectorStoreService,
    EmojiFragment,
)
from langchain_emoji.server.utils.model import (
    RestfulModel,
    SystemErrorCode,
)

logger = logging.getLogger(__name__)

vector_store_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])


class AddEmojiBody(BaseModel):
    content: str = Field(description="表情描述")
    filename: str = Field(description="表情文件名")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "xxxx",
                    "filename": "xxxx",
                }
            ]
        }
    }


class RagEmojiBody(BaseModel):
    prompt: str = Field(description="表情描述")
    filenames: List[str] = Field(default=[], description="表情文件名称列表")

    model_config = {
        "json_schema_extra": {
            "examples": [{"prompt": "xxxx", "filenames": ["xxx", "xxx"]}]
        }
    }


class DelEmojiBody(BaseModel):
    vdb_ids: List[str] = Field(description="文章向量数据库ID")
    filenames: List[str] = Field(default=[], description="表情文件名称列表")
    model_config = {
        "json_schema_extra": {
            "examples": [{"vdb_ids": ["xxxx"], "filenames": ["xxx", "xxx"]}]
        }
    }


@vector_store_router.post(
    "/vector_store/add_emoji",
    response_model=RestfulModel[Any | None],
    tags=["VectorStore"],
)
def add_emoji(request: Request, body: AddEmojiBody) -> RestfulModel:
    """
    New article into vector database
    """
    service = request.state.injector.get(VectorStoreService)
    try:
        return RestfulModel(
            data=service.add_emoji(
                content=body.content,
                filename=body.filename,
            )
        )
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


@vector_store_router.post(
    "/vector_store/rag_emoji",
    response_model=RestfulModel[List[EmojiFragment] | None],
    tags=["VectorStore"],
)
def rag_emoji(request: Request, body: RagEmojiBody) -> RestfulModel:
    """
    Recall articles from vector database
    """
    service = request.state.injector.get(VectorStoreService)
    try:
        return RestfulModel(
            data=service.rag_emoji(prompt=body.prompt, filenames=body.filenames)
        )
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)


@vector_store_router.post(
    "/vector_store/del_emoji",
    response_model=RestfulModel[List[dict] | None],
    tags=["VectorStore"],
)
def del_emoji(request: Request, body: DelEmojiBody) -> RestfulModel:
    """
    Delete articles from vector database
    """
    service = request.state.injector.get(VectorStoreService)
    try:
        return RestfulModel(
            data=service.del_emoji(vdb_ids=body.vdb_ids, filenames=body.filenames)
        )
    except Exception as e:
        logger.exception(e)
        return RestfulModel(code=SystemErrorCode, msg=str(e), data=None)
