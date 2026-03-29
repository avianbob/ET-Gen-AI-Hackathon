"""
JWT token handling for authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.repurpose_settings import settings
from app.services.repurpose.database.models import TokenData, UserModel

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, username: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's database ID
        username: User's username
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))

        if user_id is None or username is None:
            return None

        return TokenData(user_id=user_id, username=username, exp=exp)

    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserModel]:
    """
    Get the current authenticated user from the request.

    This is a dependency that can be used in route handlers.
    Returns None if no valid token is provided (allows anonymous access).

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        UserModel if authenticated, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials
    token_data = decode_access_token(token)

    if token_data is None:
        return None

    # Get user from database
    try:
        from app.services.repurpose.database import get_database
        from app.services.repurpose.database.repositories import UserRepository

        db = await get_database()
        if db is None:
            return None

        repo = UserRepository(db)
        user = await repo.find_by_id(token_data.user_id)

        if user is None or not user.is_active:
            return None

        return user

    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserModel:
    """
    Get the current authenticated user (required).

    Raises HTTPException if not authenticated.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        UserModel

    Raises:
        HTTPException: If not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user(credentials)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_admin_user(
    user: UserModel = Depends(get_current_user_required)
) -> UserModel:
    """
    Get the current user if they are an admin.

    Args:
        user: Current authenticated user

    Returns:
        UserModel if admin

    Raises:
        HTTPException: If not an admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user
