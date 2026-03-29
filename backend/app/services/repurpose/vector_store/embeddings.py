"""
Embedding Manager for generating vector embeddings.
Uses sentence-transformers for high-quality semantic embeddings.
"""

import logging
from typing import List, Optional, Union
from functools import lru_cache

logger = logging.getLogger(__name__)

# Singleton instance
_embedding_manager: Optional["EmbeddingManager"] = None


class EmbeddingManager:
    """
    Manages embedding generation using sentence-transformers.
    Optimized for biomedical/pharmaceutical text.
    """

    # Available models (from most to least specialized for biomedical)
    MODELS = {
        "biomedical": "pritamdeka/S-PubMedBert-MS-MARCO",  # Best for biomedical
        "scientific": "allenai/scibert_scivocab_uncased",  # Good for scientific
        "general": "all-MiniLM-L6-v2",  # Fast, general purpose
        "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # Multilingual
    }

    DEFAULT_MODEL = "general"  # Start with general for faster loading

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding manager.

        Args:
            model_name: Name of the model to use (key from MODELS dict or HuggingFace model ID)
        """
        self._model = None
        self._model_name = None

        # Resolve model name
        if model_name is None:
            model_name = self.DEFAULT_MODEL

        if model_name in self.MODELS:
            self._model_id = self.MODELS[model_name]
        else:
            self._model_id = model_name

        logger.info(f"EmbeddingManager initialized with model: {self._model_id}")

    def _load_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {self._model_id}")
                self._model = SentenceTransformer(self._model_id)
                self._model_name = self._model_id
                logger.info(f"Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model {self._model_id}: {e}")
                # Fallback to simple model
                logger.info("Falling back to all-MiniLM-L6-v2")
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._model_name = "all-MiniLM-L6-v2"

    @property
    def model(self):
        """Get the embedding model (lazy loaded)."""
        self._load_model()
        return self._model

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    def embed(self, texts: Union[str, List[str]], show_progress: bool = False) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]

        self._load_model()

        embeddings = self._model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        return self.embed(query)[0]

    def embed_documents(self, documents: List[str], show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.

        Args:
            documents: List of document texts
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        return self.embed(documents, show_progress=show_progress)


class ChromaEmbeddingFunction:
    """
    Adapter class to use EmbeddingManager with ChromaDB's embedding function interface.
    Implements the chromadb.EmbeddingFunction protocol.
    """

    def __init__(self, embedding_manager: Optional[EmbeddingManager] = None):
        """
        Initialize with an embedding manager.

        Args:
            embedding_manager: EmbeddingManager instance (uses singleton if None)
        """
        self._manager = embedding_manager or get_embedding_manager()
        # Instance-level name attribute (required by ChromaDB)
        self._name = "custom_embedding_function"

    def name(self) -> str:
        """Return the name of this embedding function (ChromaDB requirement)."""
        return self._name

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for ChromaDB.

        Args:
            input: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            if not input:
                return []
            return self._manager.embed(input)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return empty embeddings to avoid breaking the pipeline
            return []

    def embed_query(self, input) -> List[List[float]]:
        """Embed query text(s) — required by ChromaDB 1.4.1 for collection.query()."""
        if isinstance(input, str):
            input = [input]
        return self.__call__(input)

    def __repr__(self) -> str:
        return f"ChromaEmbeddingFunction(name={self._name})"


def get_embedding_manager(model_name: Optional[str] = None) -> EmbeddingManager:
    """
    Get or create the singleton embedding manager.

    Args:
        model_name: Optional model name to use

    Returns:
        EmbeddingManager instance
    """
    global _embedding_manager

    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager(model_name=model_name)

    return _embedding_manager
