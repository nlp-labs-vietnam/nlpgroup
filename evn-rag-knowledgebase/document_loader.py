"""
Document Loader — Tải và phân đoạn văn bản pháp lý tiếng Việt.

Hỗ trợ định dạng: PDF, DOCX.
Xử lý đặc thù VN: bảo toàn số điều/khoản, trích xuất metadata văn bản.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Iterator


# Regex nhận dạng số điều khoản VN
_ARTICLE_RE = re.compile(
    r"(Điều\s+\d+[\.\:]|Khoản\s+\d+[\.\:]|Mục\s+[IVXLCDM]+[\.\:])",
    re.UNICODE,
)

_CHUNK_MAX_TOKENS = 512
_CHUNK_OVERLAP_TOKENS = 64


class LegalDocumentLoader:
    """
    Tải tài liệu pháp lý và chia thành các đoạn (chunks) có cấu trúc.

    Ví dụ
    -----
    >>> loader = LegalDocumentLoader()
    >>> chunks = loader.load_and_chunk("docs/legal/quy_hoach_dien_viii.pdf")
    >>> print(f"Đã chia thành {len(chunks)} đoạn.")
    """

    def load_and_chunk(self, file_path: str | Path) -> list[dict]:
        """
        Tải file và trả về danh sách các đoạn (chunk).

        Returns
        -------
        list of dict, mỗi dict gồm:
            - text: nội dung đoạn văn
            - metadata: {source, page, article, document_type}
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            raw_pages = list(self._load_pdf(path))
        elif suffix in {".docx", ".doc"}:
            raw_pages = list(self._load_docx(path))
        else:
            raise ValueError(f"Định dạng không hỗ trợ: {suffix}")

        return list(self._chunk_pages(raw_pages, source=path.name))

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def _load_pdf(self, path: Path) -> Iterator[dict]:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("Cài đặt pdfplumber: pip install pdfplumber")

        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                yield {"text": text, "page": i}

    def _load_docx(self, path: Path) -> Iterator[dict]:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("Cài đặt python-docx: pip install python-docx")

        doc = Document(str(path))
        full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        yield {"text": full_text, "page": 1}

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_pages(self, pages: list[dict], source: str) -> Iterator[dict]:
        """Chia nhỏ theo ranh giới điều khoản, giữ overlap."""
        for page_info in pages:
            text: str = page_info["text"]
            if not text.strip():
                continue

            # Tách tại ranh giới điều/khoản
            segments = _ARTICLE_RE.split(text)
            buffer = ""
            current_article = ""

            for seg in segments:
                if _ARTICLE_RE.match(seg):
                    current_article = seg.strip()
                    continue

                buffer += seg
                words = buffer.split()

                if len(words) >= _CHUNK_MAX_TOKENS:
                    # Cắt chunk
                    chunk_text = " ".join(words[:_CHUNK_MAX_TOKENS])
                    overlap_text = " ".join(words[_CHUNK_MAX_TOKENS - _CHUNK_OVERLAP_TOKENS:])
                    yield {
                        "text": chunk_text,
                        "metadata": {
                            "source": source,
                            "page": page_info["page"],
                            "article": current_article,
                        },
                    }
                    buffer = overlap_text

            if buffer.strip():
                yield {
                    "text": buffer.strip(),
                    "metadata": {
                        "source": source,
                        "page": page_info["page"],
                        "article": current_article,
                    },
                }
