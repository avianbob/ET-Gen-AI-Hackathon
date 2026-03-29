"""
Knowledge Base for pharmaceutical RAG.
Manages collections of pharmaceutical knowledge for semantic retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .chroma_client import ChromaClient, get_chroma_client
from .embeddings import EmbeddingManager, ChromaEmbeddingFunction, get_embedding_manager

logger = logging.getLogger(__name__)

# Singleton instance
_knowledge_base: Optional["KnowledgeBase"] = None

# Collection names
COLLECTIONS = {
    "drug_mechanisms": "drug_mechanisms",
    "disease_pathways": "disease_pathways",
    "clinical_guidelines": "clinical_guidelines",
    "drug_interactions": "drug_interactions",
    "repurposing_cases": "repurposing_cases",
}


class KnowledgeBase:
    """
    Manages pharmaceutical knowledge for RAG retrieval.
    """

    def __init__(
        self,
        chroma_client: Optional[ChromaClient] = None,
        embedding_manager: Optional[EmbeddingManager] = None
    ):
        """
        Initialize the knowledge base.

        Args:
            chroma_client: ChromaDB client instance
            embedding_manager: Embedding manager instance
        """
        self._chroma = chroma_client or get_chroma_client()
        self._embeddings = embedding_manager or get_embedding_manager()
        self._embedding_function = ChromaEmbeddingFunction(self._embeddings)

        # Initialize collections
        self._collections = {}
        for key, name in COLLECTIONS.items():
            self._collections[key] = self._chroma.get_or_create_collection(
                name=name,
                metadata={"created": datetime.utcnow().isoformat()},
                embedding_function=self._embedding_function
            )

        logger.info(f"KnowledgeBase initialized with {len(self._collections)} collections")

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to a collection.

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs

        Returns:
            True if successful
        """
        if collection_name not in self._collections:
            logger.error(f"Collection '{collection_name}' not found")
            return False

        try:
            collection = self._collections[collection_name]

            # Generate IDs if not provided
            if ids is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                ids = [f"{collection_name}_{timestamp}_{i}" for i in range(len(documents))]

            # Ensure metadatas is provided
            if metadatas is None:
                metadatas = [{"added": datetime.utcnow().isoformat()} for _ in documents]

            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents to '{collection_name}': {e}")
            return False

    def query(
        self,
        query: str,
        collection_names: Optional[List[str]] = None,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base for relevant documents.

        Args:
            query: Search query
            collection_names: Collections to search (all if None)
            n_results: Number of results per collection
            where: Optional metadata filter

        Returns:
            List of relevant documents with metadata and scores
        """
        if collection_names is None:
            collection_names = list(self._collections.keys())

        all_results = []

        for name in collection_names:
            if name not in self._collections:
                continue

            try:
                collection = self._collections[name]
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where
                )

                # Process results
                if results and results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        result = {
                            "collection": name,
                            "document": doc,
                            "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                            "id": results['ids'][0][i] if results['ids'] else None,
                            "distance": results['distances'][0][i] if results.get('distances') else None,
                        }
                        all_results.append(result)

            except Exception as e:
                logger.error(f"Query failed for collection '{name}': {e}")

        # Sort by distance (lower is better)
        all_results.sort(key=lambda x: x.get('distance', float('inf')))

        return all_results[:n_results * 2]  # Return top results across all collections

    def query_for_drug(
        self,
        drug_name: str,
        indication: Optional[str] = None,
        n_results: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query knowledge base for information about a specific drug.

        Args:
            drug_name: Name of the drug
            indication: Optional specific indication to focus on
            n_results: Number of results

        Returns:
            Dict with results grouped by collection type
        """
        # Build query based on drug and optional indication
        if indication:
            query = f"{drug_name} {indication} mechanism treatment efficacy"
        else:
            query = f"{drug_name} mechanism of action therapeutic uses indications"

        results = self.query(query, n_results=n_results)

        # Group by collection
        grouped = {}
        for result in results:
            collection = result['collection']
            if collection not in grouped:
                grouped[collection] = []
            grouped[collection].append(result)

        return grouped

    def get_context_for_synthesis(
        self,
        drug_name: str,
        indications: List[str],
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for LLM synthesis.

        Args:
            drug_name: Name of the drug
            indications: List of potential indications
            max_tokens: Approximate max tokens for context

        Returns:
            Formatted context string
        """
        # Check if knowledge base has any data first
        if not self.is_populated():
            return ""

        context_parts = []
        char_limit = max_tokens * 4  # Rough char to token ratio

        try:
            # Query for drug mechanisms
            mechanism_results = self.query(
                f"{drug_name} mechanism of action pharmacology",
                collection_names=["drug_mechanisms"],
                n_results=3
            )

            if mechanism_results:
                context_parts.append("## Drug Mechanism Knowledge:")
                for r in mechanism_results:
                    doc = r.get('document', '')
                    if doc:
                        context_parts.append(f"- {doc[:500]}")

            # Query for each indication
            for indication in indications[:3]:  # Limit to top 3
                if not indication or indication == "Unknown Indication":
                    continue

                indication_results = self.query(
                    f"{drug_name} {indication} treatment evidence",
                    collection_names=["disease_pathways", "repurposing_cases", "clinical_guidelines"],
                    n_results=2
                )

                if indication_results:
                    context_parts.append(f"\n## Knowledge for {indication}:")
                    for r in indication_results:
                        doc = r.get('document', '')
                        if doc:
                            context_parts.append(f"- {doc[:400]}")

        except Exception as e:
            logger.warning(f"Error during RAG context retrieval: {e}", exc_info=True)
            return ""

        # Combine and truncate
        context = "\n".join(context_parts)
        if len(context) > char_limit:
            context = context[:char_limit] + "..."

        return context

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.

        Returns:
            Dict with collection stats
        """
        stats = {}
        for name, collection in self._collections.items():
            try:
                count = collection.count()
                stats[name] = {
                    "document_count": count,
                    "collection_name": COLLECTIONS.get(name, name)
                }
            except Exception as e:
                stats[name] = {"error": str(e)}

        return stats

    def is_populated(self) -> bool:
        """
        Check if the knowledge base has been populated with data.

        Returns:
            True if at least one collection has documents
        """
        for collection in self._collections.values():
            try:
                if collection.count() > 0:
                    return True
            except:
                pass
        return False


def get_knowledge_base() -> KnowledgeBase:
    """
    Get or create the singleton knowledge base.

    Returns:
        KnowledgeBase instance
    """
    global _knowledge_base

    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()

    return _knowledge_base
