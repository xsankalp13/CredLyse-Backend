"""
Authentication Routes

Handles user signup and login endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def signup(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Create a new user account.
    
    **Flow:**
    1. Check if email already exists in database
    2. Hash the password using bcrypt
    3. Create new user record
    4. Return user data (without password)
    
    Args:
        user_data: User registration data (email, password, full_name, role).
        db: Database session.
        
    Returns:
        UserResponse: Created user data.
        
    Raises:
        HTTPException: 400 if email already exists.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Authenticate user and return JWT access token.
    
    **Flow:**
    1. Find user by email (username field contains email)
    2. Verify password against stored hash
    3. Generate JWT access token
    4. Return token
    
    Note: Uses OAuth2PasswordRequestForm for compatibility with
    Swagger UI's built-in authorization feature.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.
        
    Returns:
        Token: JWT access token and token type.
        
    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user ID as subject
    access_token = create_access_token(subject=user.id)
    
    return Token(access_token=access_token, token_type="bearer")
