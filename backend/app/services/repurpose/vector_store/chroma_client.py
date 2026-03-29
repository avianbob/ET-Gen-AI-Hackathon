"""
ChromaDB Client wrapper for vector database operations.
Provides persistent storage for pharmaceutical knowledge embeddings.
"""

import os
import logging
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.repurpose_settings import settings

logger = logging.getLogger(__name__)

# Singleton instance
_chroma_client: Optional["ChromaClient"] = None


class ChromaClient:
    """
    Wrapper for ChromaDB client with persistent storage.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory for persistent storage
        """
        self.persist_directory = persist_directory or settings.VECTOR_DB_DIR

        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        logger.info(f"ChromaDB initialized at: {self.persist_directory}")

    @property
    def client(self) -> chromadb.ClientAPI:
        """Get the underlying ChromaDB client."""
        return self._client

    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[dict] = None,
        embedding_function=None
    ):
        """
        Get or create a collection.

        Args:
            name: Collection name
            metadata: Optional metadata for the collection
            embedding_function: Optional embedding function

        Returns:
            ChromaDB collection
        """
        return self._client.get_or_create_collection(
            name=name,
            metadata=metadata,
            embedding_function=embedding_function
        )

    def get_collection(self, name: str, embedding_function=None):
        """
        Get an existing collection.

        Args:
            name: Collection name
            embedding_function: Optional embedding function

        Returns:
            ChromaDB collection or None if not found
        """
        try:
            return self._client.get_collection(
                name=name,
                embedding_function=embedding_function
            )
        except Exception as e:
            logger.warning(f"Collection '{name}' not found: {e}")
            return None

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: Collection name

        Returns:
            True if deleted successfully
        """
        try:
            self._client.delete_collection(name=name)
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{name}': {e}")
            return False

    def list_collections(self) -> list:
        """
        List all collections.

        Returns:
            List of collection names
        """
        collections = self._client.list_collections()
        return [c.name for c in collections]

    def reset(self):
        """Reset the entire database (use with caution)."""
        self._client.reset()
        logger.warning("ChromaDB has been reset!")


def get_chroma_client() -> ChromaClient:
    """
    Get or create the singleton ChromaDB client.

    Returns:
        ChromaClient instance
    """
    global _chroma_client

    if _chroma_client is None:
        _chroma_client = ChromaClient()

    return _chroma_client
