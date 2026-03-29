"""
Supabase client initialization and connection management.
Provides async client for database operations and auth.

Optional dependency: install `supabase` if you use Supabase-backed features.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.repurpose_settings import settings
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("database.supabase")

# Global Supabase client instance
_supabase_client: Optional[Any] = None


def get_supabase_client() -> Optional[Any]:
    """
    Get or create the Supabase client instance.

    Returns:
        Supabase client if configured, None otherwise
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in environment.")
        return None

    try:
        from supabase import create_client
    except ImportError:
        logger.warning("Supabase SDK not installed. Run: pip install supabase")
        return None

    try:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def get_supabase_admin_client() -> Optional[Any]:
    """
    Get Supabase client with service role key for admin operations.
    Use this for server-side operations that bypass RLS.

    Returns:
        Supabase admin client if configured, None otherwise
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Supabase admin client not configured. Set SUPABASE_SERVICE_ROLE_KEY.")
        return None

    try:
        from supabase import create_client
    except ImportError:
        logger.warning("Supabase SDK not installed. Run: pip install supabase")
        return None

    try:
        return create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {e}")
        return None


class SupabaseRepository:
    """Base repository class for Supabase operations."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.client = get_supabase_client()
        self.logger = get_logger(f"database.supabase.{table_name}")

    @property
    def table(self):
        """Get the table reference."""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        return self.client.table(self.table_name)

    async def create(self, data: dict) -> Optional[dict]:
        """Insert a new record."""
        try:
            result = self.table.insert(data).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Create failed: {e}")
            raise

    async def find_by_id(self, id: str) -> Optional[dict]:
        """Find a record by ID."""
        try:
            result = self.table.select("*").eq("id", id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Find by ID failed: {e}")
            return None

    async def find_by_field(self, field: str, value: str) -> list:
        """Find records by field value."""
        try:
            result = self.table.select("*").eq(field, value).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Find by field failed: {e}")
            return []

    async def update(self, id: str, data: dict) -> Optional[dict]:
        """Update a record by ID."""
        try:
            result = self.table.update(data).eq("id", id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise

    async def delete(self, id: str) -> bool:
        """Delete a record by ID."""
        try:
            self.table.delete().eq("id", id).execute()
            return True
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return False


class UserIntegrationsRepository(SupabaseRepository):
    """Repository for user_integrations table."""

    def __init__(self):
        super().__init__("user_integrations")

    async def get_user_integrations(self, user_id: str) -> list:
        """Get all integrations for a user."""
        return await self.find_by_field("user_id", user_id)

    async def get_active_integration(self, user_id: str, integration_name: str) -> Optional[dict]:
        """Get an active integration by name for a user."""
        try:
            result = self.table.select("*").eq("user_id", user_id).eq("integration_name", integration_name).eq("is_active", True).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Get active integration failed: {e}")
            return None

    async def increment_usage(self, id: str) -> None:
        """Increment usage count and update last_used_at."""
        try:
            self.client.rpc("increment_integration_usage", {"integration_id": id}).execute()
        except Exception as e:
            self.logger.error(f"Increment usage failed: {e}")


class SearchHistoryRepository(SupabaseRepository):
    """Repository for search_history table."""

    def __init__(self):
        super().__init__("search_history")

    async def get_user_history(self, user_id: str, limit: int = 20) -> list:
        """Get recent search history for a user."""
        try:
            result = self.table.select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Get user history failed: {e}")
            return []

    async def get_popular_drugs(self, limit: int = 10) -> list:
        """Get most searched drugs."""
        try:
            result = self.client.rpc("get_popular_drugs", {"limit_count": limit}).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Get popular drugs failed: {e}")
            return []


class SavedOpportunitiesRepository(SupabaseRepository):
    """Repository for saved_opportunities table."""

    def __init__(self):
        super().__init__("saved_opportunities")

    async def get_user_opportunities(self, user_id: str, status: Optional[str] = None) -> list:
        """Get saved opportunities for a user, optionally filtered by status."""
        try:
            query = self.table.select("*").eq("user_id", user_id)
            if status:
                query = query.eq("status", status)
            result = query.order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Get user opportunities failed: {e}")
            return []

    async def update_status(self, id: str, status: str, notes: Optional[str] = None) -> Optional[dict]:
        """Update opportunity status and optionally notes."""
        data: dict = {"status": status}
        if notes is not None:
            data["notes"] = notes
        # DB trigger set_updated_at() sets updated_at on row update
        return await self.update(id, data)


class MarketDataCacheRepository(SupabaseRepository):
    """Repository for market_data_cache table."""

    def __init__(self):
        super().__init__("market_data_cache")

    async def get_cached_market_data(self, indication: str) -> Optional[dict]:
        """Get cached market data for an indication if not expired."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            result = self.table.select("*").eq("indication", indication).gt("expires_at", now_iso).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Get cached market data failed: {e}")
            return None

    async def cache_market_data(self, indication: str, data: dict, ttl_days: int = 30) -> Optional[dict]:
        """Cache market data for an indication."""
        try:
            now = datetime.now(timezone.utc)
            expires = now + timedelta(days=ttl_days)
            cache_data = {
                "indication": indication,
                "market_size_usd": data.get("market_size_usd"),
                "cagr": data.get("cagr"),
                "patient_population": data.get("patient_population"),
                "geographic_breakdown": data.get("geographic_breakdown"),
                "key_players": data.get("key_players"),
                "data_source": data.get("data_source"),
                "cached_at": now.isoformat(),
                "expires_at": expires.isoformat(),
            }
            result = self.table.upsert(cache_data, on_conflict="indication").execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.logger.error(f"Cache market data failed: {e}")
            return None


# Factory functions for dependency injection
def get_user_integrations_repository() -> UserIntegrationsRepository:
    return UserIntegrationsRepository()


def get_search_history_repository() -> SearchHistoryRepository:
    return SearchHistoryRepository()


def get_saved_opportunities_repository() -> SavedOpportunitiesRepository:
    return SavedOpportunitiesRepository()


def get_market_data_cache_repository() -> MarketDataCacheRepository:
    return MarketDataCacheRepository()
