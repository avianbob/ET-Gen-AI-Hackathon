"""
Authentication API Routes - User registration, login, and profile management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from typing import Optional

from app.services.repurpose.utils.logger import get_logger
from app.services.repurpose.database.models import (
    UserModel, UserCreate, UserLogin, UserPublic, Token
)
from app.services.repurpose.auth import create_access_token, hash_password, verify_password
from app.services.repurpose.auth.jwt import get_current_user, get_current_user_required
from app.repurpose_settings import settings

logger = get_logger("api.auth")

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.

    Args:
        user_data: User registration data

    Returns:
        Created user information
    """
    from app.services.repurpose.database import get_database
    from app.services.repurpose.database.repositories import UserRepository

    # Check if MongoDB is enabled
    db = await get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available. User registration requires MongoDB."
        )

    repo = UserRepository(db)

    # Check if username already exists
    existing = await repo.find_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing = await repo.find_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = UserModel(
        username=user_data.username,
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_admin=False,
    )

    user_id = await repo.create(user)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    logger.info(f"New user registered: {user_data.username}")

    return UserPublic(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        search_count=0
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return access token.

    Args:
        credentials: Login credentials (username/email and password)

    Returns:
        JWT access token
    """
    from app.services.repurpose.database import get_database
    from app.services.repurpose.database.repositories import UserRepository

    db = await get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    repo = UserRepository(db)

    # Find user by username or email
    user = await repo.find_by_username_or_email(credentials.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Update last login
    await repo.update_last_login(user.id)

    # Create access token
    access_token = create_access_token(user.id, user.username)

    logger.info(f"User logged in: {user.username}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserPublic)
async def get_current_user_info(user: UserModel = Depends(get_current_user_required)):
    """
    Get current authenticated user's information.

    Returns:
        Current user information
    """
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        search_count=user.search_count
    )


@router.put("/me")
async def update_current_user(
    updates: dict,
    user: UserModel = Depends(get_current_user_required)
):
    """
    Update current user's profile.

    Args:
        updates: Fields to update (full_name, preferences)

    Returns:
        Updated user information
    """
    from app.services.repurpose.database import get_database
    from app.services.repurpose.database.repositories import UserRepository

    db = await get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    repo = UserRepository(db)

    # Only allow certain fields to be updated
    allowed_fields = {"full_name", "preferences"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    success = await repo.update(user.id, filtered_updates)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

    # Get updated user
    updated_user = await repo.find_by_id(user.id)

    return UserPublic(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        search_count=updated_user.search_count
    )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    user: UserModel = Depends(get_current_user_required)
):
    """
    Change current user's password.

    Args:
        current_password: Current password
        new_password: New password (min 8 characters)

    Returns:
        Success message
    """
    from app.services.repurpose.database import get_database
    from app.services.repurpose.database.repositories import UserRepository

    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )

    db = await get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    repo = UserRepository(db)

    # Update password
    new_hash = hash_password(new_password)
    success = await repo.update(user.id, {"hashed_password": new_hash})

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

    logger.info(f"Password changed for user: {user.username}")

    return {"message": "Password updated successfully"}


@router.get("/status")
async def auth_status(user: Optional[UserModel] = Depends(get_current_user)):
    """
    Check authentication status.

    Returns:
        Authentication status and user info if logged in
    """
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    return {"authenticated": False, "user": None}
