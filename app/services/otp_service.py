"""
OTP Service

Handles OTP generation, storage, and verification.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.otp_code import OTPCode
from app.models.enums import OTPPurpose


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    return str(secrets.randbelow(900000) + 100000)


def hash_otp(code: str) -> str:
    """Hash an OTP code using SHA-256."""
    return hashlib.sha256(code.encode()).hexdigest()


async def create_otp(
    db: AsyncSession,
    email: str,
    purpose: OTPPurpose,
) -> str:
    """
    Create and store a new OTP for the given email.
    
    Invalidates any existing unused OTPs for the same email and purpose.
    
    Args:
        db: Database session.
        email: Email address to create OTP for.
        purpose: Purpose of the OTP.
        
    Returns:
        str: The plain text OTP code (to be sent via email).
    """
    # Invalidate existing unused OTPs for this email and purpose
    await db.execute(
        delete(OTPCode).where(
            and_(
                OTPCode.email == email.lower(),
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
            )
        )
    )
    
    # Generate new OTP
    plain_otp = generate_otp()
    otp_hash = hash_otp(plain_otp)
    
    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.OTP_EXPIRE_MINUTES
    )
    
    # Create OTP record
    otp_record = OTPCode(
        email=email.lower(),
        code_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at,
    )
    
    db.add(otp_record)
    await db.commit()
    
    return plain_otp


async def verify_otp(
    db: AsyncSession,
    email: str,
    code: str,
    purpose: OTPPurpose,
) -> bool:
    """
    Verify an OTP code.
    
    Args:
        db: Database session.
        email: Email address.
        code: OTP code to verify.
        purpose: Expected purpose of the OTP.
        
    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    code_hash = hash_otp(code)
    
    # Find valid OTP
    result = await db.execute(
        select(OTPCode).where(
            and_(
                OTPCode.email == email.lower(),
                OTPCode.code_hash == code_hash,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
                OTPCode.expires_at > datetime.now(timezone.utc),
            )
        )
    )
    otp_record = result.scalar_one_or_none()
    
    if not otp_record:
        return False
    
    # Mark OTP as used
    otp_record.is_used = True
    otp_record.used_at = datetime.now(timezone.utc)
    await db.commit()
    
    return True


async def can_resend_otp(
    db: AsyncSession,
    email: str,
    purpose: OTPPurpose,
) -> tuple[bool, Optional[int]]:
    """
    Check if an OTP can be resent (rate limiting).
    
    Args:
        db: Database session.
        email: Email address.
        purpose: OTP purpose.
        
    Returns:
        tuple: (can_resend, seconds_remaining)
    """
    cooldown_seconds = settings.OTP_RESEND_COOLDOWN_SECONDS
    cooldown_threshold = datetime.now(timezone.utc) - timedelta(seconds=cooldown_seconds)
    
    # Find most recent OTP for this email and purpose
    result = await db.execute(
        select(OTPCode)
        .where(
            and_(
                OTPCode.email == email.lower(),
                OTPCode.purpose == purpose,
                OTPCode.created_at > cooldown_threshold,
            )
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    recent_otp = result.scalar_one_or_none()
    
    if not recent_otp:
        return True, None
        
    # Calculate remaining cooldown
    elapsed = (datetime.now(timezone.utc) - recent_otp.created_at).total_seconds()
    remaining = int(cooldown_seconds - elapsed)
    
    if remaining <= 0:
        return True, None
        
    return False, remaining


async def cleanup_expired_otps(db: AsyncSession) -> int:
    """
    Remove expired and used OTP codes.
    
    Returns:
        int: Number of OTPs deleted.
    """
    result = await db.execute(
        delete(OTPCode).where(
            (OTPCode.expires_at < datetime.now(timezone.utc)) | 
            (OTPCode.is_used == True)
        )
    )
    await db.commit()
    return result.rowcount or 0
