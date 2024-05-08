from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import Any, Iterable, List, Optional


class EmojiChroma(Chroma):

    def add_original_texts_with_filename(
        self,
        filename: str,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        timeout: Optional[int] = None,
        batch_size: int = 1000,
        **kwargs: Any,
    ) -> List[str]:
        if not metadatas:
            metadatas = {
                "filename": filename,
            }
        return self.add_texts(
            texts=texts,
            metadatas=metadatas,
        )

    def similarity_search_by_filenames(
        self, query: str, filenames: List[str], k: int = 4
    ) -> List[Document]:
        where = None
        if len(filenames) > 0:
            where = {"filename": {"$in": filenames}}

        return self.similarity_search(query, k=k, filter=where)

    def delete_texts_with_filenames(
        self,
        document_ids: List[str],
        filenames: List[str] = [],
        batch_size: int = 20,
        expr: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        common_ids = document_ids

        if len(filenames) > 0:
            where = {"filename": {"$in": filenames}}
            result = self._collection.get(where=where)
            print(result)
            common_ids = [value for value in result.get("ids") if value in document_ids]

        return self.delete(
            ids=common_ids,
        )
