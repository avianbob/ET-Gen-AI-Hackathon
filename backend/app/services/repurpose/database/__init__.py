"""
Database module for MongoDB integration.
Provides persistent storage for users, search history, and cached results.
"""

from .mongodb import MongoDB, get_database
from .models import UserModel, SearchHistoryModel, CachedResultModel
from .repositories import UserRepository, SearchHistoryRepository, CacheRepository

__all__ = [
    "MongoDB",
    "get_database",
    "UserModel",
    "SearchHistoryModel",
    "CachedResultModel",
    "UserRepository",
    "SearchHistoryRepository",
    "CacheRepository",
]
