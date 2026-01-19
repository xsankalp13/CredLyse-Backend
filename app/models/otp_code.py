"""
OTP Code Model

Stores OTP verification codes for email verification and password reset.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Enum, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import OTPPurpose


class OTPCode(Base):
    """
    OTP Code model for email verification and password reset.
    
    Attributes:
        id: UUID primary key.
        email: Email address this OTP is for (indexed for fast lookups).
        code_hash: Hashed OTP code (6-digit).
        purpose: Purpose of OTP (EMAIL_VERIFICATION, PASSWORD_RESET).
        expires_at: When the OTP expires (10 minutes from creation).
        used_at: When the OTP was consumed (null if unused).
        created_at: Creation timestamp.
    """
    
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    purpose: Mapped[OTPPurpose] = mapped_column(
        Enum(OTPPurpose, name="otp_purpose", create_constraint=True),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<OTPCode(id={self.id}, email={self.email}, purpose={self.purpose})>"
