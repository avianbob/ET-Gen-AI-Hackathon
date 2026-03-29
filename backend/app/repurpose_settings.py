"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from app.services.repurpose.utils.gemini_model_util import normalize_gemini_model as _normalize_gemini_model_env


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    GEMINI_API_KEY: str = "your_gemini_api_key_here"
    LENS_API_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    DRUGBANK_API_KEY: Optional[str] = None
    PATENTSVIEW_API_KEY: Optional[str] = None  # Optional: PatentsView v2 API key for live patent search

    # Supabase Settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    # gemini-pro removed from Google API; .env may still set it — validated to a live model id
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @field_validator("GEMINI_MODEL", mode="before")
    @classmethod
    def _coerce_gemini_model(cls, v):
        return _normalize_gemini_model_env(str(v) if v is not None else "")

    # Application Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # Cache Settings
    CACHE_TTL: int = 604800  # 7 days in seconds
    CACHE_DIR: str = "data/cache"
    VECTOR_DB_DIR: str = "data/vector_db"

    # MongoDB Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "drug_repurposing"
    USE_MONGODB: bool = False  # Set to True to use MongoDB instead of JSON cache

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # API Settings
    API_TIMEOUT: int = 60  # Increased timeout for external APIs
    MAX_RETRIES: int = 2  # Reduced retries to speed up overall response
    RETRY_DELAY: int = 1  # seconds

    # Rate Limits - Existing Agents
    PUBMED_RATE_LIMIT: float = 3.0  # requests per second
    CLINICAL_TRIALS_RATE_LIMIT: float = 1.0
    CHEMBL_RATE_LIMIT: float = 2.0
    LENS_RATE_LIMIT: float = 0.5
    USPTO_RATE_LIMIT: float = 5.0  # PatentsView API - generous limits, no key needed

    # Rate Limits - New Agents (Phase 2)
    OPENFDA_RATE_LIMIT: float = 4.0  # 240 req/min without API key
    OPENTARGETS_RATE_LIMIT: float = 2.0  # GraphQL API
    SEMANTIC_SCHOLAR_RATE_LIMIT: float = 0.33  # 100 req/5min = ~0.33/sec
    DAILYMED_RATE_LIMIT: float = 2.0
    KEGG_RATE_LIMIT: float = 1.0
    UNIPROT_RATE_LIMIT: float = 3.0
    RXNORM_RATE_LIMIT: float = 5.0  # 20 req/sec max
    WHO_RATE_LIMIT: float = 1.0
    DRUGBANK_RATE_LIMIT: float = 1.0
    ORANGE_BOOK_RATE_LIMIT: float = 1.0

    # CORS Settings (PharmAI Vite dev/preview + common local ports)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:4173",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
