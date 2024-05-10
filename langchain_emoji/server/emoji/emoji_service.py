from injector import inject
from langchain_emoji.components.llm.llm_component import LLMComponent
from langchain_emoji.components.trace.trace_component import TraceComponent
from langchain_emoji.components.minio.minio_component import MinioComponent
from langchain_emoji.components.vector_store.vector_store_component import (
    VectorStoreComponent,
)

from langchain_emoji.server.emoji.emoji_prompt import (
    RESPONSE_TEMPLATE,
    ZHIPUAI_RESPONSE_TEMPLATE,
)
from langchain.schema.output_parser import StrOutputParser
from pydantic import BaseModel, Field
import logging
import tiktoken
from langchain_emoji.settings.settings import Settings
from langchain.schema.document import Document
from langchain.schema.runnable import (
    Runnable,
    RunnableLambda,
    RunnableBranch,
    RunnableMap,
)
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.messages import BaseMessage
from langchain.schema.retriever import BaseRetriever
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema.runnable import ConfigurableField
from operator import itemgetter

from langchain_community.callbacks import get_openai_callback
from langchain_emoji.components.llm.custom.zhipuai import get_zhipuai_callback
from langchain_emoji.paths import local_data_path
from uuid import UUID
from json.decoder import JSONDecodeError
import json
import base64
import re
from typing import (
    List,
    Optional,
    Sequence,
    Dict,
    Any,
)


logger = logging.getLogger(__name__)


class TokenInfo(BaseModel):
    model: str
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embedding_tokens: int = 0
    successful_requests: int = 0
    total_cost: float = 0.0

    def clear(self):
        self.total_tokens = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.successful_requests: int = 0
        self.total_cost: float = 0.0


class EmojiRequest(BaseModel):
    prompt: str
    req_id: str
    llm: str = Field(default="openai", description="大模型")

    model_config = {
        "json_schema_extra": {
            "examples": [{"prompt": "xxxx", "req_id": "xxxx", "llm": "xxx"}]
        }
    }


class EmojiInfo(BaseModel):
    filename: str
    content: str


class EmojiDetail(BaseModel):
    download_link: Optional[str] = None
    base64: str


class EmojiResponse(BaseModel):
    run_id: UUID
    emojiinfo: EmojiInfo
    emojidetail: EmojiDetail
    tokeninfo: TokenInfo


"""
读取chain run_id的回调
"""


class ReadRunIdAsyncHandler(AsyncCallbackHandler):

    def __init__(self):
        self.runid: UUID = None

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""
        if not self.runid:
            self.runid = run_id

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any: ...

    async def on_retriever_end(
        self,
        documents: Sequence[Document],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run on retriever end."""
        # TODO 目前没有合适过滤选项，获取原文链接还是采用全局变量获取
        ...

    def get_runid(self) -> UUID:
        return self.runid


def fix_json(json_str: str) -> dict:
    # 使用正则表达式替换掉重复的逗号
    fixed_json_str = re.sub(r",\s*}", "}", json_str)
    fixed_json_str = re.sub(r",\s*]", "]", fixed_json_str)

    # 尝试加载修复后的JSON字符串
    return json.loads(fixed_json_str)


class EmojiService:

    @inject
    def __init__(
        self,
        llm_component: LLMComponent,
        vector_component: VectorStoreComponent,
        trace_component: TraceComponent,
        minio_component: MinioComponent,
        settings: Settings,
    ) -> None:
        self.settings = settings
        self.llm_service = llm_component
        self.vector_service = vector_component
        self.trace_service = trace_component
        self.minio_service = minio_component
        self.chain = self.create_chain(
            self.llm_service.llm,
            self.get_vector_retriever(),
        )

    def num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(self.llm_service.modelname)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    """
    防止返回不是json格式，增加校验处理
    """

    def output_handle(self, output: str) -> dict:
        try:
            # 找到json子串并加载为字典
            start_index = output.find("{")
            end_index = output.rfind("}") + 1
            json_str = output[start_index:end_index]

            # 加载为字典
            return json.loads(json_str)
        except JSONDecodeError as e:
            logger.exception(e)
            return fix_json(json_str)

    async def get_emoji(self, body: EmojiRequest) -> EmojiResponse | None:
        logger.info(body)
        token_callback = (
            get_openai_callback if body.llm == "openai" else get_zhipuai_callback
        )
        with token_callback() as cb:
            read_runid = ReadRunIdAsyncHandler()  # 读取runid回调
            result = await self.chain.ainvoke(
                input={"prompt": body.prompt, "llm": body.llm},
                config={
                    "metadata": {
                        "req_id": body.req_id,
                    },
                    "configurable": {"llm": body.llm},
                    "callbacks": [cb, read_runid],
                },
            )

            logger.info(result)
            emojiinfo = EmojiInfo(**result)

            embed_tokens = self.vector_service.embedcom.total_tokens
            tokeninfo = TokenInfo(
                model=body.llm,
                total_tokens=cb.total_tokens + int(embed_tokens / 10),
                prompt_tokens=cb.prompt_tokens,
                completion_tokens=cb.completion_tokens,
                embedding_tokens=int(embed_tokens / 10),
                successful_requests=cb.successful_requests,
                total_cost=cb.total_cost,
            )

            resobj = EmojiResponse(
                run_id=read_runid.get_runid(),
                emojiinfo=emojiinfo,
                emojidetail=self.get_file_desc(emojiinfo),
                tokeninfo=tokeninfo,
            )
            return resobj

    def get_file_desc(self, info: EmojiInfo) -> EmojiDetail:
        logger.info(self.settings.dataset.mode)
        if self.settings.dataset.mode == "local":
            emoji_file = (
                local_data_path / self.settings.dataset.name / "emo" / info.filename
            )
            with open(emoji_file, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                file_base64 = encoded_string.decode("utf-8")
                return EmojiDetail(base64=file_base64)
        elif self.settings.dataset.mode == "minio":
            file_base64 = self.minio_service.get_file_base64(info.filename)
            file_download_link = self.minio_service.get_download_link(info.filename)
            return EmojiDetail(base64=file_base64, download_link=file_download_link)

    def get_vector_retriever(self):
        base_vector = self.vector_service.vector_store.as_retriever().configurable_alternatives(
            # This gives this field an id
            # When configuring the end runnable, we can then use this id to configure this field
            ConfigurableField(id="vectordb"),
            default_key=self.settings.vectorstore.database,
        )

        return base_vector.with_config(run_name="VectorRetriever")

    def create_retriever_chain(self, retriever: BaseRetriever) -> Runnable:
        return (
            RunnableLambda(itemgetter("prompt")).with_config(
                run_name="Itemgetter:prompt"
            )
            | retriever
        ).with_config(run_name="RetrievalChain")

    def format_docs(self, docs: Sequence[Document]) -> str:
        formatted_docs = []
        for i, doc in enumerate(docs):
            filename = doc.metadata.get("filename")
            doc_string = (
                f"<emoji id='{i}' metadata={filename}>{doc.page_content}</emoji>"
            )
            formatted_docs.append(doc_string)
        return "\n".join(formatted_docs)

    def create_chain(
        self,
        llm: BaseLanguageModel,
        retriever: BaseRetriever,
    ) -> Runnable:
        retriever_chain = self.create_retriever_chain(retriever) | RunnableLambda(
            self.format_docs
        )
        _context = RunnableMap(
            {
                "context": retriever_chain.with_config(run_name="RetrievalChain"),
                "prompt": RunnableLambda(itemgetter("prompt")).with_config(
                    run_name="Itemgetter:prompt"
                ),
                "llm": RunnableLambda(itemgetter("llm")).with_config(
                    run_name="Itemgetter:llm"
                ),
            }
        )
        _prompt = RunnableBranch(
            (
                RunnableLambda(
                    lambda x: bool(
                        x.get("llm") == "openai" or x.get("llm") == "deepseek"
                    )
                ).with_config(run_name="CheckLLM"),
                ChatPromptTemplate.from_messages(
                    [
                        ("human", RESPONSE_TEMPLATE),
                    ]
                ).with_config(run_name="OpenaiPrompt"),
            ),
            (
                ChatPromptTemplate.from_messages(
                    [
                        ("human", ZHIPUAI_RESPONSE_TEMPLATE),
                    ]
                ).with_config(run_name="ZhipuaiPrompt")
            ),
        ).with_config(run_name="ChoiceLLMPrompt")

        response_synthesizer = (_prompt | llm | StrOutputParser()).with_config(
            run_name="GenerateResponse",
        ) | RunnableLambda(self.output_handle).with_config(run_name="ResponseHandle")

        return (
            {
                "prompt": RunnableLambda(itemgetter("prompt")).with_config(
                    run_name="Itemgetter:prompt"
                ),
                "llm": RunnableLambda(itemgetter("llm")).with_config(
                    run_name="Itemgetter:llm"
                ),
            }
            | _context
            | response_synthesizer
        ).with_config(run_name="EmojiChain")
