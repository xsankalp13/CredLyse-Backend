"""
Certificate Routes

Endpoints for claiming and verifying certificates.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.services import certificate_service


router = APIRouter(prefix="", tags=["Certificates"])


@router.post(
    "/courses/{course_id}/claim-certificate",
    summary="Claim course certificate",
)
async def claim_certificate(
    course_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Claim a certificate for a completed course.
    
    **Requirements:**
    - User must be enrolled.
    - All videos must be watched.
    - All quizzes must be passed.
    
    **Action:**
    - Generates a PDF certificate.
    - Marks enrollment as completed.
    - Returns the certificate URL.
    
    Args:
        course_id: Course ID.
        current_user: Authenticated student.
        db: Database session.
        
    Returns:
        Certificate details and PDF URL.
    """
    certificate = await certificate_service.issue_certificate(
        user=current_user,
        playlist_id=course_id,
        db=db,
    )
    
    return {
        "certificate_id": str(certificate.id),
        "pdf_url": certificate.pdf_url,
        "issued_at": certificate.issued_at,
        "message": "Certificate issued successfully!",
    }


@router.get(
    "/certificates/{certificate_id}",
    summary="Verify certificate",
)
async def verify_certificate(
    certificate_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Verify a certificate by ID.
    
    Public endpoint for verification links/QR codes.
    
    Args:
        certificate_id: Certificate UUID.
        db: Database session.
        
    Returns:
        Certificate details.
    """
    certificate = await certificate_service.get_certificate(certificate_id, db)
    
    return {
        "valid": True,
        "certificate_id": str(certificate.id),
        "user_id": str(certificate.user_id),
        "course_id": certificate.playlist_id,
        "issued_at": certificate.issued_at,
        "pdf_url": certificate.pdf_url,
    }
