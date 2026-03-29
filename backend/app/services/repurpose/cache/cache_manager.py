"""
Cache Manager - Caches search results for fast retrieval and demo reliability.
Uses JSON files for simplicity and portability.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.repurpose_settings import settings
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("cache")


class CacheManager:
    """Manages caching of search results using JSON files."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files (uses settings if not provided)
        """
        self.cache_dir = Path(cache_dir or settings.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(seconds=settings.CACHE_TTL)

        logger.info(f"Cache manager initialized: {self.cache_dir}")
        logger.info(f"Cache TTL: {settings.CACHE_TTL} seconds ({settings.CACHE_TTL / 86400:.1f} days)")

    def _get_cache_file(self, drug_name: str) -> Path:
        """
        Get cache file path for a drug.

        Args:
            drug_name: Drug name

        Returns:
            Path to cache file
        """
        # Normalize drug name for file system
        normalized_name = drug_name.lower().strip().replace(" ", "_")
        return self.cache_dir / f"{normalized_name}.json"

    async def get_cached_result(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result if available and fresh.

        Args:
            drug_name: Drug name to look up

        Returns:
            Cached result dictionary or None if not found/expired
        """
        cache_file = self._get_cache_file(drug_name)

        if not cache_file.exists():
            logger.debug(f"Cache miss: {drug_name} (file not found)")
            return None

        try:
            # Read cache file
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check freshness
            cached_time = datetime.fromisoformat(data.get('timestamp', ''))
            age = datetime.now() - cached_time

            if age > self.ttl:
                logger.info(f"Cache expired: {drug_name} (age: {age.days} days)")
                return None

            logger.info(f"Cache hit: {drug_name} (age: {age.seconds}s)")
            return data

        except Exception as e:
            logger.error(f"Cache read error for {drug_name}: {e}")
            return None

    async def cache_result(self, drug_name: str, result: Dict[str, Any]):
        """
        Store search result in cache.

        Args:
            drug_name: Drug name
            result: Search result dictionary to cache
        """
        cache_file = self._get_cache_file(drug_name)

        try:
            # Ensure result has timestamp
            if 'timestamp' not in result:
                result['timestamp'] = datetime.now().isoformat()

            # Write to cache file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)

            logger.info(f"Cached result for: {drug_name}")

        except Exception as e:
            logger.error(f"Cache write error for {drug_name}: {e}")

    def clear_cache(self):
        """Clear all cached results."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def clear_drug_cache(self, drug_name: str) -> bool:
        """
        Clear cached result for a specific drug.

        Args:
            drug_name: Drug name to clear from cache

        Returns:
            True if cache was cleared, False otherwise
        """
        cache_file = self._get_cache_file(drug_name)

        try:
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for: {drug_name}")
                return True
            else:
                logger.debug(f"No cache file found for: {drug_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to clear cache for {drug_name}: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))

        return {
            "total_entries": len(cache_files),
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": settings.CACHE_TTL,
            "ttl_days": settings.CACHE_TTL / 86400
        }
