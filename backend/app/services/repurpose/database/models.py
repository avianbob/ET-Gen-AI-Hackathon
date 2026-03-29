"""
Database models for MongoDB collections.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


class BaseDBModel(BaseModel):
    """Base model for database documents."""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserModel(BaseDBModel):
    """User document model."""

    username: str
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)

    # Usage tracking
    search_count: int = 0
    last_search_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion."""
        data = self.model_dump(by_alias=True, exclude={"id"})
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserModel":
        """Create model from MongoDB document."""
        return cls(**data)


class UserPublic(BaseModel):
    """Public user information (without sensitive data)."""

    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    search_count: int = 0


class SearchHistoryModel(BaseDBModel):
    """Search history document model."""

    user_id: Optional[str] = None  # None for anonymous searches
    session_id: str
    drug_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Search metadata
    execution_time: float = 0.0
    cached: bool = False
    evidence_count: int = 0
    indications_count: int = 0

    # Top results summary
    top_indication: Optional[str] = None
    top_confidence: Optional[float] = None

    # Full results (optional, for history replay)
    results: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion."""
        data = self.model_dump(by_alias=True, exclude={"id"})
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchHistoryModel":
        """Create model from MongoDB document."""
        return cls(**data)


class CachedResultModel(BaseDBModel):
    """Cached search result document model."""

    drug_name: str  # Normalized drug name (lowercase, underscores)
    original_name: str  # Original drug name as searched
    expires_at: datetime

    # Full search results
    results: Dict[str, Any]

    # Metadata
    hit_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion."""
        data = self.model_dump(by_alias=True, exclude={"id"})
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedResultModel":
        """Create model from MongoDB document."""
        return cls(**data)

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.utcnow() > self.expires_at


# Request/Response models for API

class UserCreate(BaseModel):
    """User creation request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    username: str  # Can be username or email
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Decoded token data."""
    user_id: str
    username: str
    exp: datetime
