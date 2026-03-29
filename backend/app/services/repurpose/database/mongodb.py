"""
MongoDB client wrapper using Motor for async operations.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.repurpose_settings import settings

logger = logging.getLogger(__name__)

# Singleton instance
_mongodb: Optional["MongoDB"] = None


class MongoDB:
    """
    MongoDB client wrapper with connection management.
    """

    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        """
        Initialize MongoDB connection.

        Args:
            connection_string: MongoDB connection URI
            database_name: Database name to use
        """
        self._connection_string = connection_string or getattr(settings, "MONGODB_URI", "mongodb://localhost:27017")
        self._database_name = database_name or getattr(settings, "MONGODB_DATABASE", "drug_repurposing")

        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to MongoDB.

        Returns:
            True if connected successfully
        """
        if self._connected:
            return True

        try:
            self._client = AsyncIOMotorClient(
                self._connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )

            # Verify connection
            await self._client.admin.command("ping")

            self._db = self._client[self._database_name]
            self._connected = True

            logger.info(f"Connected to MongoDB: {self._database_name}")

            # Create indexes
            await self._create_indexes()

            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"MongoDB connection failed: {e}")
            self._connected = False
            return False

        except Exception as e:
            logger.error(f"Unexpected MongoDB error: {e}")
            self._connected = False
            return False

    async def _create_indexes(self):
        """Create necessary database indexes."""
        try:
            # Users collection indexes
            await self._db.users.create_index("email", unique=True)
            await self._db.users.create_index("username", unique=True)

            # Search history indexes
            await self._db.search_history.create_index("user_id")
            await self._db.search_history.create_index("drug_name")
            await self._db.search_history.create_index("timestamp")
            await self._db.search_history.create_index([("user_id", 1), ("timestamp", -1)])

            # Cache indexes
            await self._db.cache.create_index("drug_name", unique=True)
            await self._db.cache.create_index("expires_at")
            await self._db.cache.create_index("created_at")

            logger.info("MongoDB indexes created")

        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")

    async def disconnect(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")

    @property
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        return self._connected

    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        """Get the database instance."""
        return self._db

    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """Get the client instance."""
        return self._client

    # Collection accessors
    @property
    def users(self):
        """Get users collection."""
        return self._db.users if self._db is not None else None

    @property
    def search_history(self):
        """Get search_history collection."""
        return self._db.search_history if self._db is not None else None

    @property
    def cache(self):
        """Get cache collection."""
        return self._db.cache if self._db is not None else None


async def get_database() -> Optional[MongoDB]:
    """
    Get or create the singleton MongoDB instance.

    Returns:
        MongoDB instance or None if connection fails
    """
    global _mongodb

    if _mongodb is None:
        _mongodb = MongoDB()

    if _mongodb.is_connected is False:
        await _mongodb.connect()

    if _mongodb.is_connected:
        return _mongodb
    return None


async def close_database():
    """Close the database connection."""
    global _mongodb

    if _mongodb:
        await _mongodb.disconnect()
        _mongodb = None
