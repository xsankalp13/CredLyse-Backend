"""
Certificate Service

Handles certificate eligibility checking and PDF generation.
"""

import os
import uuid
from datetime import datetime
from typing import Tuple, List, Optional

from fastapi import HTTPException, status
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.playlist import Playlist
from app.models.video import Video
from app.models.enrollment import Enrollment
from app.models.video_progress import VideoProgress
from app.models.certificate import Certificate
from app.models.enums import WatchStatus


# Directory to store generated certificates
CERTIFICATES_DIR = "static/certificates"


async def check_eligibility(
    user_id: uuid.UUID,
    playlist_id: int,
    db: AsyncSession,
) -> Tuple[bool, List[str]]:
    """
    Check if a user is eligible for a certificate in a course.
    
    Strict Criteria:
    1. User must be enrolled.
    2. User must have a progress record for EVERY video.
    3. Every video must be WATCHED.
    4. Every video must have is_quiz_passed=True.
    
    Args:
        user_id: User ID.
        playlist_id: Playlist ID.
        db: Database session.
        
    Returns:
        Tuple of (is_eligible, list_of_missing_requirements).
    """
    # 1. Fetch Enrollment
    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.playlist_id == playlist_id,
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    
    if not enrollment:
        return False, ["User is not enrolled in this course"]
    
    # 2. Fetch all videos in the playlist
    videos_result = await db.execute(
        select(Video).where(Video.playlist_id == playlist_id)
    )
    videos = list(videos_result.scalars().all())
    
    if not videos:
        return False, ["Course has no videos"]
    
    # 3. Fetch all progress records for this enrollment
    progress_result = await db.execute(
        select(VideoProgress).where(VideoProgress.enrollment_id == enrollment.id)
    )
    progress_records = list(progress_result.scalars().all())
    
    # Map video_id to progress record
    progress_map = {p.video_id: p for p in progress_records}
    
    missing = []
    
    for video in videos:
        progress = progress_map.get(video.id)
        
        if not progress:
            missing.append(f"Video '{video.title}' not started")
            continue
            
        if progress.watch_status != WatchStatus.WATCHED:
            missing.append(f"Video '{video.title}' not fully watched")
            
        if not progress.is_quiz_passed:
            missing.append(f"Video '{video.title}' quiz not passed")
            
    if missing:
        return False, missing
        
    return True, []


def generate_certificate_pdf(certificate: Certificate, user_name: str, course_title: str) -> str:
    """
    Generate a PDF certificate using ReportLab.
    
    Args:
        certificate: Certificate model instance.
        user_name: Name of the student.
        course_title: Title of the course.
        
    Returns:
        Relative URL path to the generated PDF.
    """
    # Ensure directory exists
    os.makedirs(CERTIFICATES_DIR, exist_ok=True)
    
    filename = f"{certificate.id}.pdf"
    filepath = os.path.join(CERTIFICATES_DIR, filename)
    
    # Create PDF
    c = canvas.Canvas(filepath, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Draw Border
    c.setStrokeColorRGB(0.2, 0.2, 0.8)
    c.setLineWidth(5)
    c.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch)
    
    # Title
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(width / 2, height - 2.5 * inch, "Certificate of Completion")
    
    # Subtitle
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, height - 3.2 * inch, "This is to certify that")
    
    # Student Name
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - 4 * inch, user_name)
    
    # Completed Text
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, height - 4.8 * inch, "has successfully completed the course")
    
    # Course Title
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(width / 2, height - 5.5 * inch, course_title)
    
    # Date and ID
    c.setFont("Helvetica", 12)
    date_str = certificate.issued_at.strftime("%B %d, %Y")
    c.drawString(1 * inch, 1 * inch, f"Date: {date_str}")
    c.drawString(width - 3.5 * inch, 1 * inch, f"Certificate ID: {str(certificate.id)[:8]}")
    
    c.save()
    
    return f"/{CERTIFICATES_DIR}/{filename}"


async def issue_certificate(
    user: User,
    playlist_id: int,
    db: AsyncSession,
) -> Certificate:
    """
    Issue a certificate to a user for a course.
    
    Flow:
    1. Check if certificate already exists (idempotency).
    2. Check eligibility (strict).
    3. Create Certificate record.
    4. Generate PDF.
    5. Update Enrollment status.
    
    Args:
        user: Student user.
        playlist_id: Course ID.
        db: Database session.
        
    Returns:
        Certificate object.
        
    Raises:
        HTTPException: 400 if not eligible.
    """
    # 1. Check existing certificate
    result = await db.execute(
        select(Certificate).where(
            Certificate.user_id == user.id,
            Certificate.playlist_id == playlist_id,
        )
    )
    existing_cert = result.scalar_one_or_none()
    
    if existing_cert:
        return existing_cert
    
    # 2. Check eligibility
    is_eligible, missing = await check_eligibility(user.id, playlist_id, db)
    
    if not is_eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Not eligible for certificate yet",
                "missing_requirements": missing
            }
        )
    
    # Fetch playlist for title
    playlist_result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id)
    )
    playlist = playlist_result.scalar_one_or_none()
    
    # 3. Create Certificate record
    certificate = Certificate(
        id=uuid.uuid4(),
        user_id=user.id,
        playlist_id=playlist_id,
        issued_at=datetime.utcnow(),
    )
    db.add(certificate)
    
    # 4. Generate PDF
    pdf_url = generate_certificate_pdf(certificate, user.full_name, playlist.title)
    certificate.pdf_url = pdf_url
    
    # 5. Update Enrollment
    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.playlist_id == playlist_id,
        )
    )
    enrollment = enrollment_result.scalar_one()
    enrollment.is_completed = True
    enrollment.certificate_url = pdf_url
    
    await db.commit()
    await db.refresh(certificate)
    
    return certificate


async def get_certificate(
    certificate_id: uuid.UUID,
    db: AsyncSession,
) -> Certificate:
    """
    Get certificate by ID.
    
    Args:
        certificate_id: UUID.
        db: Database session.
        
    Returns:
        Certificate object.
        
    Raises:
        HTTPException: 404 if not found.
    """
    result = await db.execute(
        select(Certificate).where(Certificate.id == certificate_id)
    )
    certificate = result.scalar_one_or_none()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
        
    return certificate
