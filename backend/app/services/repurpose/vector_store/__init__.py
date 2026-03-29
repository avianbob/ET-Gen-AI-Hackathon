"""
Vector Store module for RAG functionality.
Provides ChromaDB integration for semantic search over pharmaceutical knowledge.
"""

from .chroma_client import ChromaClient, get_chroma_client
from .embeddings import EmbeddingManager, get_embedding_manager
from .knowledge_base import KnowledgeBase, get_knowledge_base

__all__ = [
    "ChromaClient",
    "get_chroma_client",
    "EmbeddingManager",
    "get_embedding_manager",
    "KnowledgeBase",
    "get_knowledge_base",
]
