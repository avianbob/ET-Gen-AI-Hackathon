"""
Repository classes for database operations.
Provides async data access patterns for MongoDB collections.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId

from .mongodb import MongoDB, get_database
from .models import UserModel, SearchHistoryModel, CachedResultModel
from app.repurpose_settings import settings

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: MongoDB):
        self._db = db

    @property
    def collection(self):
        return self._db.users

    async def create(self, user: UserModel) -> Optional[str]:
        """
        Create a new user.

        Args:
            user: User model to create

        Returns:
            Created user ID or None if failed
        """
        try:
            result = await self.collection.insert_one(user.to_dict())
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    async def find_by_id(self, user_id: str) -> Optional[UserModel]:
        """Find user by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
            return UserModel.from_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to find user by ID: {e}")
            return None

    async def find_by_email(self, email: str) -> Optional[UserModel]:
        """Find user by email."""
        try:
            doc = await self.collection.find_one({"email": email.lower()})
            return UserModel.from_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to find user by email: {e}")
            return None

    async def find_by_username(self, username: str) -> Optional[UserModel]:
        """Find user by username."""
        try:
            doc = await self.collection.find_one({"username": username})
            return UserModel.from_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to find user by username: {e}")
            return None

    async def find_by_username_or_email(self, identifier: str) -> Optional[UserModel]:
        """Find user by username or email."""
        try:
            doc = await self.collection.find_one({
                "$or": [
                    {"username": identifier},
                    {"email": identifier.lower()}
                ]
            })
            return UserModel.from_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to find user: {e}")
            return None

    async def update(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user fields."""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        return await self.update(user_id, {"last_login": datetime.utcnow()})

    async def increment_search_count(self, user_id: str) -> bool:
        """Increment user's search count."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": {"search_count": 1},
                    "$set": {
                        "last_search_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to increment search count: {e}")
            return False

    async def delete(self, user_id: str) -> bool:
        """Delete a user."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False


class SearchHistoryRepository:
    """Repository for search history operations."""

    def __init__(self, db: MongoDB):
        self._db = db

    @property
    def collection(self):
        return self._db.search_history

    async def create(self, history: SearchHistoryModel) -> Optional[str]:
        """
        Create a search history entry.

        Args:
            history: Search history model

        Returns:
            Created entry ID or None
        """
        try:
            result = await self.collection.insert_one(history.to_dict())
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create search history: {e}")
            return None

    async def find_by_user(
        self,
        user_id: str,
        limit: int = 20,
        skip: int = 0
    ) -> List[SearchHistoryModel]:
        """Get search history for a user."""
        try:
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).skip(skip).limit(limit)

            results = []
            async for doc in cursor:
                results.append(SearchHistoryModel.from_dict(doc))
            return results
        except Exception as e:
            logger.error(f"Failed to get user search history: {e}")
            return []

    async def find_by_drug(
        self,
        drug_name: str,
        limit: int = 10
    ) -> List[SearchHistoryModel]:
        """Get search history for a drug."""
        try:
            # Case-insensitive search
            cursor = self.collection.find(
                {"drug_name": {"$regex": f"^{drug_name}$", "$options": "i"}}
            ).sort("timestamp", -1).limit(limit)

            results = []
            async for doc in cursor:
                results.append(SearchHistoryModel.from_dict(doc))
            return results
        except Exception as e:
            logger.error(f"Failed to get drug search history: {e}")
            return []

    async def get_recent_searches(
        self,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> List[SearchHistoryModel]:
        """Get recent searches, optionally filtered by user."""
        try:
            query = {"user_id": user_id} if user_id else {}
            cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)

            results = []
            async for doc in cursor:
                results.append(SearchHistoryModel.from_dict(doc))
            return results
        except Exception as e:
            logger.error(f"Failed to get recent searches: {e}")
            return []

    async def get_popular_drugs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most searched drugs."""
        try:
            pipeline = [
                {"$group": {
                    "_id": {"$toLower": "$drug_name"},
                    "count": {"$sum": 1},
                    "last_searched": {"$max": "$timestamp"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            cursor = self.collection.aggregate(pipeline)
            return [doc async for doc in cursor]
        except Exception as e:
            logger.error(f"Failed to get popular drugs: {e}")
            return []

    async def delete_user_history(self, user_id: str) -> int:
        """Delete all search history for a user."""
        try:
            result = await self.collection.delete_many({"user_id": user_id})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete user history: {e}")
            return 0


class CacheRepository:
    """Repository for cached search results."""

    def __init__(self, db: MongoDB):
        self._db = db
        self._ttl = getattr(settings, "CACHE_TTL", 604800)  # 7 days

    @property
    def collection(self):
        return self._db.cache

    def _normalize_drug_name(self, name: str) -> str:
        """Normalize drug name for cache key."""
        return name.lower().replace(" ", "_").replace("-", "_")

    async def get(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached results for a drug.

        Args:
            drug_name: Drug name to look up

        Returns:
            Cached results or None if not found/expired
        """
        try:
            normalized = self._normalize_drug_name(drug_name)
            doc = await self.collection.find_one({"drug_name": normalized})

            if not doc:
                return None

            cache_entry = CachedResultModel.from_dict(doc)

            # Check expiration
            if cache_entry.is_expired():
                await self.delete(drug_name)
                return None

            # Update hit count and last accessed
            await self.collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$inc": {"hit_count": 1},
                    "$set": {"last_accessed": datetime.utcnow()}
                }
            )

            results = cache_entry.results
            results["cached"] = True
            results["cache_age"] = (datetime.utcnow() - cache_entry.created_at).total_seconds()

            return results

        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            return None

    async def set(self, drug_name: str, results: Dict[str, Any]) -> bool:
        """
        Cache search results.

        Args:
            drug_name: Drug name
            results: Search results to cache

        Returns:
            True if cached successfully
        """
        try:
            normalized = self._normalize_drug_name(drug_name)
            expires_at = datetime.utcnow() + timedelta(seconds=self._ttl)

            cache_entry = CachedResultModel(
                drug_name=normalized,
                original_name=drug_name,
                expires_at=expires_at,
                results=results,
                hit_count=0
            )

            # Upsert (update or insert)
            await self.collection.update_one(
                {"drug_name": normalized},
                {"$set": cache_entry.to_dict()},
                upsert=True
            )

            logger.info(f"Cached results for: {drug_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
            return False

    async def delete(self, drug_name: str) -> bool:
        """Delete cached results for a drug."""
        try:
            normalized = self._normalize_drug_name(drug_name)
            result = await self.collection.delete_one({"drug_name": normalized})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False

    async def clear_all(self) -> int:
        """Clear all cached results."""
        try:
            result = await self.collection.delete_many({})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    async def clear_expired(self) -> int:
        """Clear expired cache entries."""
        try:
            result = await self.collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total = await self.collection.count_documents({})
            expired = await self.collection.count_documents({
                "expires_at": {"$lt": datetime.utcnow()}
            })

            # Get total hits
            pipeline = [
                {"$group": {"_id": None, "total_hits": {"$sum": "$hit_count"}}}
            ]
            cursor = self.collection.aggregate(pipeline)
            hits_doc = await cursor.to_list(length=1)
            total_hits = hits_doc[0]["total_hits"] if hits_doc else 0

            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "total_hits": total_hits,
                "ttl_seconds": self._ttl
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Factory functions for getting repositories

async def get_user_repository() -> Optional[UserRepository]:
    """Get user repository instance."""
    db = await get_database()
    if db is not None:
        return UserRepository(db)
    return None


async def get_search_history_repository() -> Optional[SearchHistoryRepository]:
    """Get search history repository instance."""
    db = await get_database()
    if db is not None:
        return SearchHistoryRepository(db)
    return None


async def get_cache_repository() -> Optional[CacheRepository]:
    """Get cache repository instance."""
    db = await get_database()
    if db is not None:
        return CacheRepository(db)
    return None
