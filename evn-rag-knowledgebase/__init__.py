"""
evn-rag-knowledgebase
=====================
Hệ thống RAG (Retrieval-Augmented Generation) cho pháp lý điện mặt trời VN.
"""

from .rag_pipeline import SolarLegalRAG
from .document_loader import LegalDocumentLoader
from .embeddings import VietnameseEmbedder

__version__ = "0.1.0"
__all__ = ["SolarLegalRAG", "LegalDocumentLoader", "VietnameseEmbedder"]
