import logging

from injector import inject, singleton
from langchain_emoji.settings.settings import Settings
from langchain_emoji.components.vector_store.tencent.tencent import (
    EmojiTencentVectorDB,
    ConnectionParams,
)

logger = logging.getLogger(__name__)


@singleton
class VectorStoreComponent:
    @inject
    def __init__(self, settings: Settings) -> None:
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
            case _:
                # Should be unreachable
                # The settings validator should have caught this
                raise ValueError(
                    f"Vectorstore database {settings.vectorstore.database} not supported"
                )

    def close(self) -> None: ...
