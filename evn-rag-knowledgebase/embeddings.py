"""
Vietnamese Embedder — Tạo vector embedding cho văn bản pháp lý tiếng Việt.

Mô hình mặc định: bkai-foundation-models/vietnamese-bi-encoder (HuggingFace)
Vector store: ChromaDB (local, persistent)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional


class VietnameseEmbedder:
    """
    Wrapper tạo embedding tiếng Việt và quản lý vector store ChromaDB.

    Parameters
    ----------
    model_name : str
        Tên mô hình embedding HuggingFace.
        Các lựa chọn tốt cho tiếng Việt:
        - "bkai-foundation-models/vietnamese-bi-encoder"
        - "keepitreal/vietnamese-sbert"
        - "VoVanPhuc/sup-SimCSE-Viet-roberta-base"
    """

    def __init__(
        self,
        model_name: str = "bkai-foundation-models/vietnamese-bi-encoder",
    ) -> None:
        self.model_name = model_name
        self._model: Any = None
        self._chroma_client: Any = None

    def _ensure_model(self) -> None:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "Cài đặt sentence-transformers: pip install sentence-transformers"
                )

    def build_vector_store(
        self,
        chunks: list[dict],
        persist_dir: Optional[Path] = None,
        collection_name: str = "solar_legal_vn",
    ) -> Any:
        """
        Tạo và lưu vector store ChromaDB từ danh sách chunks.

        Parameters
        ----------
        chunks : list of dict
            Mỗi dict gồm 'text' và 'metadata'.
        persist_dir : Path, optional
            Thư mục lưu ChromaDB.
        collection_name : str
            Tên collection.

        Returns
        -------
        chromadb.Collection
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("Cài đặt chromadb: pip install chromadb")

        self._ensure_model()

        settings = chromadb.Settings(anonymized_telemetry=False)
        if persist_dir:
            persist_dir.mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=str(persist_dir), settings=settings
            )
        else:
            self._chroma_client = chromadb.Client(settings=settings)

        collection = self._chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        texts = [c["text"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]
        ids = [f"chunk_{i}" for i in range(len(chunks))]

        embeddings = self._model.encode(texts, batch_size=32, show_progress_bar=True).tolist()

        collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
        return collection

    def load_vector_store(
        self,
        persist_dir: Path,
        collection_name: str = "solar_legal_vn",
    ) -> Any:
        """Tải vector store đã lưu từ đĩa."""
        try:
            import chromadb
        except ImportError:
            raise ImportError("Cài đặt chromadb: pip install chromadb")

        self._chroma_client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        return self._chroma_client.get_collection(name=collection_name)

    def query(
        self,
        collection: Any,
        question: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Tìm kiếm các đoạn văn bản liên quan.

        Returns
        -------
        list of dict : [{"text": ..., "metadata": ..., "score": ...}]
        """
        self._ensure_model()
        query_embedding = self._model.encode([question]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({"text": doc, "metadata": meta, "score": 1.0 - dist})
        return output
