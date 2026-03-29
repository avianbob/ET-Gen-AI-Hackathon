"""
Search API Routes - Main drug repurposing search endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
import uuid
from datetime import datetime

from app.schemas.repurpose_api import DrugSearchRequest, SearchResponse, AgentResponse, EvidenceItem, IndicationResult
from app.graph.workflow import get_workflow
from app.services.repurpose.cache.cache_manager import CacheManager
from app.services.repurpose.utils.logger import get_logger
from app.services.repurpose.utils.full_report_templates import ensure_full_report_extensions_on_cache
from pydantic import BaseModel

logger = get_logger("api.search")


def _serialize_value(value: Any) -> Any:
    """Recursively serialize Pydantic models and other objects to dictionaries."""
    if isinstance(value, BaseModel):
        return value.model_dump()
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    else:
        return value


def _serialize_workflow_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize workflow result to ensure all Pydantic models are converted to dicts.

    LangGraph may store Pydantic model instances in state, which need to be
    converted to dictionaries for proper JSON serialization.
    """
    serialized = {}

    for key, value in result.items():
        serialized[key] = _serialize_value(value)

    return serialized


router = APIRouter()

# Initialize cache manager
cache = CacheManager()


@router.post("/search", response_model=SearchResponse)
async def search_drug(
    request: DrugSearchRequest,
    background_tasks: BackgroundTasks
) -> SearchResponse:
    """
    Search for drug repurposing opportunities.

    This is the main endpoint that orchestrates the entire multi-agent workflow:
    1. Checks cache for existing results
    2. Runs LangGraph workflow if not cached
    3. Returns ranked indications with evidence and AI synthesis

    Args:
        request: Drug search request with drug name and optional context
        background_tasks: FastAPI background tasks for async caching

    Returns:
        SearchResponse with ranked indications and synthesis

    Raises:
        HTTPException: On validation or execution errors
    """
    try:
        # Validate drug name
        drug_name = request.drug_name.strip()
        if not drug_name:
            raise HTTPException(status_code=400, detail="Drug name cannot be empty")

        logger.info(f"Search request received for: {drug_name}")

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Check cache first (unless force_refresh is True)
        if not request.force_refresh:
            cached_result = await cache.get_cached_result(drug_name)
            if cached_result:
                logger.info(f"Cache hit for: {drug_name}")

                # Add cache indicator to response
                cached_result["cached"] = True
                cached_result["cache_age"] = (
                    datetime.now() - datetime.fromisoformat(cached_result["timestamp"])
                ).total_seconds()

                ensure_full_report_extensions_on_cache(cached_result)

                return SearchResponse(**cached_result)

        logger.info(f"Cache miss for: {drug_name}, running workflow...")

        # Get compiled workflow
        workflow = get_workflow()

        # Prepare initial state
        initial_state = {
            "drug_name": drug_name,
            "search_context": request.context or {},
            "session_id": session_id
        }

        # Run the workflow
        logger.info(f"Starting workflow for: {drug_name}")
        result = await workflow.ainvoke(initial_state)

        # Convert Pydantic models to dictionaries for proper serialization
        serialized_result = _serialize_workflow_result(result)

        # Add metadata
        serialized_result["cached"] = False
        serialized_result["session_id"] = session_id

        # Cache the result in background
        background_tasks.add_task(cache.cache_result, drug_name, serialized_result)

        logger.info(
            f"Search completed for {drug_name}: "
            f"{len(serialized_result.get('ranked_indications', []))} indications found, "
            f"execution time: {serialized_result.get('execution_time', 0):.2f}s"
        )

        return SearchResponse(**serialized_result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Search failed for {drug_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/search/status/{session_id}")
async def get_search_status(session_id: str) -> Dict[str, Any]:
    """
    Get the status of an ongoing search by session ID.

    Note: Currently not implemented as searches complete synchronously.
    For real-time progress, use WebSocket connection.

    Args:
        session_id: Session identifier

    Returns:
        Status information
    """
    return {
        "session_id": session_id,
        "message": "Use WebSocket connection for real-time progress updates",
        "websocket_url": f"/ws/{session_id}"
    }


@router.get("/search/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Cache statistics including entry count and TTL
    """
    try:
        stats = cache.get_cache_stats()
        logger.debug(f"Cache stats requested: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/search/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Clear all cached search results.

    Returns:
        Confirmation message
    """
    try:
        cache.clear_cache()
        logger.info("Cache cleared successfully")
        return {"status": "success", "message": "Cache cleared"}

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/search/cache/{drug_name}")
async def clear_drug_cache(drug_name: str) -> Dict[str, str]:
    """
    Clear cached result for a specific drug.

    Args:
        drug_name: Drug name to clear from cache

    Returns:
        Confirmation message
    """
    try:
        cleared = cache.clear_drug_cache(drug_name)
        logger.info(f"Cache clear requested for: {drug_name}, cleared: {cleared}")
        return {
            "status": "success",
            "cleared": cleared,
            "message": f"Cache cleared for {drug_name}" if cleared else f"No cache found for {drug_name}"
        }

    except Exception as e:
        logger.error(f"Failed to clear cache for {drug_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
