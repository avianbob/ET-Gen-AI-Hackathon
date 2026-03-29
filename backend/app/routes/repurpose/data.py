"""
Data Management API Routes - Clear all platform data.
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.services.repurpose.cache.cache_manager import CacheManager
from app.services.repurpose.chat.conversation_manager import ConversationManager
from app.services.repurpose.archive.report_archive_manager import ReportArchiveManager
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("api.data")
router = APIRouter()

_cache = CacheManager()
_conv_manager = ConversationManager()
_archive = ReportArchiveManager()


@router.delete("/data/clear-all")
async def clear_all_data() -> Dict[str, Any]:
    """
    Clear ALL platform data: cache, conversations, reports.
    This is destructive and cannot be undone.
    """
    results = {
        "cache": {"status": "pending"},
        "conversations": {"status": "pending"},
        "reports": {"status": "pending"},
    }

    # 1. Clear search cache (data/cache/*.json)
    try:
        _cache.clear_cache()
        results["cache"] = {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        results["cache"] = {"status": "error", "message": str(e)}

    # 2. Clear all conversations (data/conversations/*.json)
    try:
        cleared_count = 0
        for fp in _conv_manager.conversations_dir.glob("*.json"):
            fp.unlink()
            cleared_count += 1
        results["conversations"] = {"status": "success", "cleared": cleared_count}
    except Exception as e:
        logger.error(f"Failed to clear conversations: {e}")
        results["conversations"] = {"status": "error", "message": str(e)}

    # 3. Clear all reports (data/reports/*.pdf, *.xlsx, reset metadata)
    try:
        cleared_count = 0
        for fp in _archive.archive_dir.glob("*.pdf"):
            fp.unlink()
            cleared_count += 1
        for fp in _archive.archive_dir.glob("*.xlsx"):
            fp.unlink()
            cleared_count += 1
        _archive._save_metadata([])
        results["reports"] = {"status": "success", "cleared": cleared_count}
    except Exception as e:
        logger.error(f"Failed to clear reports: {e}")
        results["reports"] = {"status": "error", "message": str(e)}

    all_success = all(r["status"] == "success" for r in results.values())
    logger.info(f"Clear all data: {'SUCCESS' if all_success else 'PARTIAL'} - {results}")

    return {
        "status": "success" if all_success else "partial",
        "message": "All data cleared" if all_success else "Some data could not be cleared",
        "details": results,
    }
