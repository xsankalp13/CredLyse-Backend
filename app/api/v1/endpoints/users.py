"""
User Routes

Endpoints for user profile management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Get the currently logged-in user's profile.
    
    This endpoint requires authentication via Bearer token.
    The token is validated by the get_current_active_user dependency.
    
    Args:
        current_user: Authenticated user from dependency.
        
    Returns:
        UserResponse: Current user's profile data.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Update the currently logged-in user's profile.
    
    Only provided fields will be updated.
    
    Args:
        user_update: Fields to update (email, full_name).
        current_user: Authenticated user from dependency.
        db: Database session.
        
    Returns:
        UserResponse: Updated user profile.
        
    Raises:
        HTTPException: 400 if new email already exists.
    """
    # Check if email is being updated and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        result = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = user_update.email
    
    # Update full_name if provided
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user
