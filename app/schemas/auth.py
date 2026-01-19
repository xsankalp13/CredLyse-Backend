"""
Auth Schemas

Pydantic models for authentication request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    """Schema for email verification request."""
    
    email: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class ResendOTPRequest(BaseModel):
    """Schema for resend OTP request."""
    
    email: EmailStr = Field(..., description="User's email address")


class ResendOTPResponse(BaseModel):
    """Schema for resend OTP response."""
    
    message: str
    cooldown_seconds: int | None = None


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication."""
    
    id_token: str = Field(..., description="Google ID token from client")


class SignupResponse(BaseModel):
    """Schema for signup response (requires email verification)."""
    
    message: str
    email: str
    requires_verification: bool = True


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    
    email: EmailStr = Field(..., description="User's email address")


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response."""
    
    message: str
    email: str


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    
    email: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
