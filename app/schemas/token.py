"""
Token Schemas

Pydantic models for JWT token handling.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for token response."""
    
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded token payload."""
    
    sub: str  # User ID
    exp: int  # Expiration timestamp
