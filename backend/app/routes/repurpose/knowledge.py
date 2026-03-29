"""
Knowledge Base API Routes - RAG knowledge management endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.repurpose.utils.logger import get_logger

logger = get_logger("api.knowledge")

router = APIRouter()


class KnowledgeQueryRequest(BaseModel):
    """Request model for knowledge base queries."""
    query: str
    collections: Optional[List[str]] = None
    n_results: int = 5


class KnowledgeQueryResponse(BaseModel):
    """Response model for knowledge base queries."""
    results: List[Dict[str, Any]]
    query: str
    total_results: int


class KnowledgeStatsResponse(BaseModel):
    """Response model for knowledge base statistics."""
    is_populated: bool
    collections: Dict[str, Any]
    total_documents: int


class InitializeResponse(BaseModel):
    """Response model for knowledge base initialization."""
    success: bool
    message: str
    documents_added: Optional[Dict[str, int]] = None


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats():
    """
    Get knowledge base statistics.

    Returns information about collections and document counts.
    """
    try:
        from app.services.repurpose.vector_store import get_knowledge_base

        kb = get_knowledge_base()
        stats = kb.get_stats()
        is_populated = kb.is_populated()

        total = sum(
            s.get("document_count", 0)
            for s in stats.values()
            if isinstance(s, dict)
        )

        return KnowledgeStatsResponse(
            is_populated=is_populated,
            collections=stats,
            total_documents=total
        )

    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize", response_model=InitializeResponse)
async def initialize_knowledge_base(background_tasks: BackgroundTasks, force: bool = False):
    """
    Initialize the knowledge base with pharmaceutical documents.

    Args:
        force: If True, reinitialize even if already populated
    """
    try:
        from app.services.repurpose.vector_store import get_knowledge_base
        from app.services.repurpose.vector_store.init_knowledge_base import populate_knowledge_base

        kb = get_knowledge_base()

        # Check if already populated
        if kb.is_populated() and not force:
            return InitializeResponse(
                success=True,
                message="Knowledge base is already populated. Use force=true to reinitialize.",
                documents_added=None
            )

        # Populate the knowledge base
        results = populate_knowledge_base(kb)

        return InitializeResponse(
            success=True,
            message="Knowledge base initialized successfully",
            documents_added=results
        )

    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge_base(request: KnowledgeQueryRequest):
    """
    Query the knowledge base for relevant documents.

    Performs semantic search across pharmaceutical knowledge collections.
    """
    try:
        from app.services.repurpose.vector_store import get_knowledge_base

        kb = get_knowledge_base()

        if not kb.is_populated():
            raise HTTPException(
                status_code=400,
                detail="Knowledge base is not populated. Call /api/knowledge/initialize first."
            )

        results = kb.query(
            query=request.query,
            collection_names=request.collections,
            n_results=request.n_results
        )

        return KnowledgeQueryResponse(
            results=results,
            query=request.query,
            total_results=len(results)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drug/{drug_name}")
async def get_drug_knowledge(drug_name: str, indication: Optional[str] = None):
    """
    Get knowledge base information for a specific drug.

    Args:
        drug_name: Name of the drug
        indication: Optional specific indication to focus on
    """
    try:
        from app.services.repurpose.vector_store import get_knowledge_base

        kb = get_knowledge_base()

        if not kb.is_populated():
            raise HTTPException(
                status_code=400,
                detail="Knowledge base is not populated. Call /api/knowledge/initialize first."
            )

        results = kb.query_for_drug(drug_name, indication)

        return {
            "drug_name": drug_name,
            "indication": indication,
            "knowledge": results,
            "total_documents": sum(len(v) for v in results.values())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Drug knowledge query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
