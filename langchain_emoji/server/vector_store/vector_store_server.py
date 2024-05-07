from injector import inject, singleton
from langchain_emoji.components.vector_store import VectorStoreComponent
from pydantic import BaseModel, Field
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmojiFragment(BaseModel):
    content: str = Field(description="表情描述段落")
    filename: Optional[str] = Field(default=-1, description="表情文件名")


@singleton
class VectorStoreService:
    @inject
    def __init__(
        self,
        vector_store: VectorStoreComponent,
    ) -> None:
        self.client = vector_store.vector_store

    def add_emoji(
        self,
        content: str,
        filename: str,
    ) -> List[str]:
        metadata = {
            "filename": filename,
        }
        return self.client.add_original_texts_with_filename(
            filename=filename, texts=[content], metadatas=[metadata]
        )

    def rag_emoji(self, prompt: str, filenames: List[str] = []) -> List[EmojiFragment]:
        fragment_list = self.client.similarity_search_by_filenames(
            query=prompt, filenames=filenames, k=3
        )
        res = []
        for fragment in fragment_list:
            res.append(
                EmojiFragment(content=fragment.page_content, **fragment.metadata)
            )
        return res

    def del_emoji(self, vdb_ids: List[str], filenames: List[str] = []) -> List[dict]:
        return self.client.delete_texts_with_filenames(
            document_ids=vdb_ids, filenames=filenames
        )
