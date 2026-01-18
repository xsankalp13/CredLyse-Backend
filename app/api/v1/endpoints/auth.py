"""
Authentication Routes

Handles user signup, login, email verification, and Google OAuth endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.enums import OTPPurpose, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.schemas.auth import (
    VerifyEmailRequest,
    ResendOTPRequest,
    ResendOTPResponse,
    GoogleAuthRequest,
    SignupResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from app.services import otp_service, email_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account (requires email verification)",
)
async def signup(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SignupResponse:
    """
    Create a new user account and send email verification OTP.
    
    **Flow:**
    1. Check if email already exists in database
    2. Hash the password using bcrypt
    3. Create new user record with is_email_verified=False
    4. Generate and send OTP to email
    5. Return success message (user must verify email before logging in)
    
    Args:
        user_data: User registration data (email, password, full_name, role).
        db: Database session.
        
    Returns:
        SignupResponse: Message with email requiring verification.
        
    Raises:
        HTTPException: 400 if email already exists.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            # User exists but not verified - resend OTP
            otp_code = await otp_service.create_otp(
                db, user_data.email, OTPPurpose.EMAIL_VERIFICATION
            )
            await email_service.send_verification_email(
                user_data.email, otp_code, existing_user.full_name
            )
            return SignupResponse(
                message="Verification code sent to your email",
                email=user_data.email,
                requires_verification=True,
            )
    
    # Create new user with hashed password
    new_user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_email_verified=False,
        auth_provider="email",
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate and send OTP
    otp_code = await otp_service.create_otp(
        db, user_data.email, OTPPurpose.EMAIL_VERIFICATION
    )
    await email_service.send_verification_email(
        user_data.email, otp_code, user_data.full_name
    )
    
    return SignupResponse(
        message="Account created! Please verify your email with the code we sent.",
        email=user_data.email,
        requires_verification=True,
    )


@router.post(
    "/verify-email",
    response_model=Token,
    summary="Verify email with OTP code",
)
async def verify_email(
    data: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Verify user's email with OTP code and return JWT token.
    
    **Flow:**
    1. Validate OTP code
    2. Mark user as email verified
    3. Return JWT access token
    
    Args:
        data: Email and OTP code.
        db: Database session.
        
    Returns:
        Token: JWT access token on successful verification.
        
    Raises:
        HTTPException: 400 if OTP is invalid or expired.
        HTTPException: 404 if user not found.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_email_verified:
        # Already verified, just return token
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token, token_type="bearer")
    
    # Verify OTP
    is_valid = await otp_service.verify_otp(
        db, data.email, data.otp, OTPPurpose.EMAIL_VERIFICATION
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )
    
    # Mark email as verified
    from datetime import datetime, timezone
    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    await db.commit()
    
    # Create access token
    access_token = create_access_token(subject=user.id)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/resend-otp",
    response_model=ResendOTPResponse,
    summary="Resend verification OTP",
)
async def resend_otp(
    data: ResendOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResendOTPResponse:
    """
    Resend email verification OTP (rate limited).
    
    Args:
        data: Email address.
        db: Database session.
        
    Returns:
        ResendOTPResponse: Success message or cooldown information.
        
    Raises:
        HTTPException: 404 if user not found.
        HTTPException: 400 if user already verified.
        HTTPException: 429 if rate limited.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )
    
    # Check rate limit
    can_resend, remaining = await otp_service.can_resend_otp(
        db, data.email, OTPPurpose.EMAIL_VERIFICATION
    )
    
    if not can_resend:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} seconds before requesting a new code",
            headers={"Retry-After": str(remaining)},
        )
    
    # Generate and send new OTP
    otp_code = await otp_service.create_otp(
        db, data.email, OTPPurpose.EMAIL_VERIFICATION
    )
    await email_service.send_verification_email(
        data.email, otp_code, user.full_name
    )
    
    return ResendOTPResponse(
        message="Verification code sent to your email",
        cooldown_seconds=settings.OTP_RESEND_COOLDOWN_SECONDS,
    )


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
    3. Check email is verified
    4. Generate JWT access token
    5. Return token
    
    Note: Uses OAuth2PasswordRequestForm for compatibility with
    Swagger UI's built-in authorization feature.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.
        
    Returns:
        Token: JWT access token and token type.
        
    Raises:
        HTTPException: 401 if credentials are invalid.
        HTTPException: 403 if email not verified.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username.lower())
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check email verification
    if not user.is_email_verified:
        # Send new OTP for convenience
        otp_code = await otp_service.create_otp(
            db, user.email, OTPPurpose.EMAIL_VERIFICATION
        )
        await email_service.send_verification_email(
            user.email, otp_code, user.full_name
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. A new verification code has been sent to your email.",
        )
    
    # Create access token with user ID as subject
    access_token = create_access_token(subject=user.id)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/google",
    response_model=Token,
    summary="Authenticate with Google OAuth",
)
async def google_auth(
    data: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Authenticate user with Google OAuth token.
    
    Accepts either an ID token or an access token from Google OAuth.
    
    **Flow:**
    1. Verify token with Google's API
    2. Extract user info (email, name, Google ID)
    3. Find or create user
    4. Return JWT access token
    
    Args:
        data: Google token from client.
        db: Database session.
        
    Returns:
        Token: JWT access token.
        
    Raises:
        HTTPException: 400 if Google token is invalid.
        HTTPException: 500 if Google verification fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Try to get user info using the token as an access token
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {data.id_token}"}
            )
            
            if response.status_code != 200:
                # If that fails, try treating it as an ID token
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={data.id_token}"
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid Google token",
                    )
                    
                google_data = response.json()
                google_id = google_data.get("sub")
                email = google_data.get("email")
                full_name = google_data.get("name", email.split("@")[0] if email else "User")
                picture_url = google_data.get("picture")
            else:
                google_data = response.json()
                google_id = google_data.get("sub")
                email = google_data.get("email")
                full_name = google_data.get("name", email.split("@")[0] if email else "User")
                picture_url = google_data.get("picture")
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify Google token",
        )
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account must have an email",
        )
    
    # Check if user exists by Google ID
    result = await db.execute(
        select(User).where(User.google_id == google_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Check if user exists by email (account linking)
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            if picture_url:
                user.profile_picture_url = picture_url
            if not user.is_email_verified:
                user.is_email_verified = True
                from datetime import datetime, timezone
                user.email_verified_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            # Create new user
            from datetime import datetime, timezone
            user = User(
                email=email.lower(),
                password_hash="",  # No password for OAuth users
                full_name=full_name,
                role=UserRole.STUDENT,
                is_email_verified=True,
                email_verified_at=datetime.now(timezone.utc),
                google_id=google_id,
                auth_provider="google",
                profile_picture_url=picture_url,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
    
    # Create access token
    access_token = create_access_token(subject=user.id)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request password reset OTP",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ForgotPasswordResponse:
    """
    Request a password reset OTP.
    
    **Flow:**
    1. Check if user exists by email
    2. Generate OTP code
    3. Send password reset email
    
    Args:
        data: Email address for password reset.
        db: Database session.
        
    Returns:
        ForgotPasswordResponse: Confirmation message.
        
    Raises:
        HTTPException: 404 if user not found.
        HTTPException: 500 if email fails to send.
    """
    email = data.email.lower()
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists for security
        # But still return success to prevent email enumeration
        return ForgotPasswordResponse(
            message="If an account exists with this email, you'll receive a reset code.",
            email=email,
        )
    
    # Check if user is OAuth-only (no password)
    if user.auth_provider != "email" and not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google sign-in. Please use Google to log in.",
        )
    
    # Check rate limiting
    can_send, remaining = await otp_service.can_resend_otp(
        db, email, OTPPurpose.PASSWORD_RESET
    )
    if not can_send:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} seconds before requesting another code",
        )
    
    # Generate and store OTP
    otp_code = await otp_service.create_otp(db, email, OTPPurpose.PASSWORD_RESET)
    
    # Send password reset email
    email_sent = await email_service.send_password_reset_email(
        to_email=email,
        otp_code=otp_code,
        full_name=user.full_name,
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email",
        )
    
    return ForgotPasswordResponse(
        message="Password reset code sent to your email",
        email=email,
    )


@router.post(
    "/reset-password",
    response_model=dict,
    summary="Reset password with OTP",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Reset password using OTP verification.
    
    **Flow:**
    1. Verify OTP code
    2. Update user's password
    3. Invalidate OTP
    
    Args:
        data: Email, OTP code, and new password.
        db: Database session.
        
    Returns:
        dict: Success message.
        
    Raises:
        HTTPException: 400 if OTP is invalid or expired.
        HTTPException: 404 if user not found.
    """
    email = data.email.lower()
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify OTP
    is_valid = await otp_service.verify_otp(
        db, email, data.otp, OTPPurpose.PASSWORD_RESET
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code. Please request a new one.",
        )
    
    # Update password
    user.password_hash = hash_password(data.new_password)
    await db.commit()
    
    return {"message": "Password reset successfully. You can now log in with your new password."}
