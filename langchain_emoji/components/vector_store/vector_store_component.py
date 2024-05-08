import logging
import os
from injector import inject, singleton
from pathlib import Path
from langchain_emoji.settings.settings import Settings
from langchain_emoji.components.vector_store.tencent.tencent import (
    EmojiTencentVectorDB,
    ConnectionParams,
)
from langchain_emoji.components.vector_store.chroma.chroma import EmojiChroma
from chromadb.config import Settings as ChromaSettings

from langchain_emoji.constants import PROJECT_ROOT_PATH
from langchain_emoji.components.embedding.embedding_component import EmbeddingComponent

logger = logging.getLogger(__name__)


@singleton
class VectorStoreComponent:
    @inject
    def __init__(self, embed: EmbeddingComponent, settings: Settings) -> None:
        match settings.vectorstore.database:
            case "tcvectordb":
                tcvectorconf = settings.vectorstore.tcvectordb
                connect_params = ConnectionParams(
                    url=tcvectorconf.url, key=tcvectorconf.api_key
                )
                self.vector_store = EmojiTencentVectorDB(
                    connection_params=connect_params,
                    database_name=tcvectorconf.database_name,
                    collection_name=tcvectorconf.collection_name,
                )
            case "chromadb":
                data_dir = PROJECT_ROOT_PATH / settings.vectorstore.chromadb.persist_dir
                persist_directory = self.create_persist_directory("chromadb", data_dir)
                collection_name = settings.vectorstore.chromadb.collection_name
                self.vector_store = EmojiChroma(
                    collection_name,
                    embed._embedding,
                    client_settings=ChromaSettings(
                        anonymized_telemetry=False,
                        is_persistent=True,
                        persist_directory=persist_directory,
                    ),
                )
            case _:
                # Should be unreachable
                # The settings validator should have caught this
                raise ValueError(
                    f"Vectorstore database {settings.vectorstore.database} not supported"
                )

    def create_persist_directory(self, vectordb: str, data_dir: Path) -> str:
        if not (os.path.exists(data_dir) and os.path.isdir(data_dir)):
            raise FileNotFoundError(f"{data_dir} Error, Please Check Config")

        persist_directory = data_dir / vectordb
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        return str(persist_directory)

    def close(self) -> None: ...
