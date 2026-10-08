"""
RAG Pipeline — Hệ thống hỏi đáp pháp lý điện mặt trời Việt Nam.

Kiến trúc:
  [PDF/DOCX] → [Chunking] → [Embedding] → [Vector DB] → [Retrieval] → [LLM] → [Trả lời TV]
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class RetrievalResult:
    """Kết quả truy xuất và trả lời từ hệ thống RAG."""

    answer: str
    sources: list[dict[str, str]] = field(default_factory=list)
    confidence: float = 0.0

    def format(self) -> str:
        lines = [self.answer, ""]
        if self.sources:
            lines.append("📄 Nguồn tham chiếu:")
            for src in self.sources:
                doc = src.get("document", "")
                article = src.get("article", "")
                lines.append(f"  • {doc}" + (f" — {article}" if article else ""))
        return "\n".join(lines)


class SolarLegalRAG:
    """
    Hệ thống RAG hỏi đáp về pháp lý điện mặt trời Việt Nam.

    Parameters
    ----------
    vector_db_path : str or Path, optional
        Đường dẫn thư mục lưu trữ ChromaDB.  Mặc định: ./data/vectordb
    llm_provider : str, optional
        Nhà cung cấp LLM: "openai" | "anthropic" | "watsonx" | "local".
    embedding_model : str, optional
        Tên mô hình embedding tiếng Việt.
        Mặc định: "bkai-foundation-models/vietnamese-bi-encoder"

    Ví dụ
    -----
    >>> rag = SolarLegalRAG()
    >>> rag.ingest_documents("docs/legal/")
    >>> result = rag.query("Quy định DPPA mới nhất năm 2024 là gì?")
    >>> print(result.format())
    """

    def __init__(
        self,
        vector_db_path: Optional[str] = None,
        llm_provider: str = "openai",
        embedding_model: str = "bkai-foundation-models/vietnamese-bi-encoder",
    ) -> None:
        self.vector_db_path = Path(vector_db_path or "data/vectordb")
        self.llm_provider = llm_provider
        self.embedding_model = embedding_model
        self._db: Any = None  # lazy init

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_documents(self, source_dir: str | Path) -> int:
        """
        Đọc và index tất cả tài liệu pháp lý trong thư mục.

        Parameters
        ----------
        source_dir : str or Path
            Thư mục chứa PDF/DOCX của văn bản pháp lý.

        Returns
        -------
        int
            Số đoạn văn bản (chunks) đã được index.
        """
        from .document_loader import LegalDocumentLoader
        from .embeddings import VietnameseEmbedder

        loader = LegalDocumentLoader()
        embedder = VietnameseEmbedder(model_name=self.embedding_model)

        source_path = Path(source_dir)
        all_chunks: list[dict] = []

        for doc_path in sorted(source_path.rglob("*.pdf")) + sorted(source_path.rglob("*.docx")):
            chunks = loader.load_and_chunk(doc_path)
            all_chunks.extend(chunks)

        self._db = embedder.build_vector_store(all_chunks, persist_dir=self.vector_db_path)
        return len(all_chunks)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> RetrievalResult:
        """
        Truy vấn hệ thống RAG bằng tiếng Việt.

        Parameters
        ----------
        question : str
            Câu hỏi tiếng Việt.
        top_k : int
            Số đoạn tài liệu tham chiếu tối đa.
        min_score : float
            Ngưỡng điểm tương đồng tối thiểu.

        Returns
        -------
        RetrievalResult
        """
        if self._db is None:
            raise RuntimeError(
                "Vector store chưa được khởi tạo. Hãy gọi ingest_documents() trước "
                "hoặc load_vector_store() từ thư mục đã lưu."
            )

        # TODO: tích hợp LLM thực tế — hiện trả về placeholder
        return RetrievalResult(
            answer=(
                f"[Demo] Câu hỏi: '{question}'\n"
                "→ Hệ thống RAG đang trong giai đoạn phát triển. "
                "Tích hợp LLM sẽ được hoàn thiện trong Phase 2."
            ),
            sources=[{"document": "Quy hoạch Điện VIII — QĐ 500/QĐ-TTg", "article": "Điều 3"}],
            confidence=0.0,
        )

    def load_vector_store(self, path: Optional[str] = None) -> None:
        """Tải Vector Store đã được lưu từ đĩa."""
        from .embeddings import VietnameseEmbedder

        load_path = Path(path) if path else self.vector_db_path
        embedder = VietnameseEmbedder(model_name=self.embedding_model)
        self._db = embedder.load_vector_store(load_path)
