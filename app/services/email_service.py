"""
Email Service

Handles sending emails for OTP verification and password reset.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings


logger = logging.getLogger(__name__)


def get_verification_email_html(otp_code: str, full_name: str) -> str:
    """Generate HTML content for verification email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%); padding: 40px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px; }}
            .otp-box {{ background: #fef2f2; border: 2px dashed #fecaca; border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0; }}
            .otp-code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #e11d48; font-family: monospace; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
            p {{ color: #374151; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 Credlyse</h1>
            </div>
            <div class="content">
                <p>Hi {full_name},</p>
                <p>Welcome to Credlyse! Please use the verification code below to complete your registration:</p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                
                <p>This code will expire in <strong>{settings.OTP_EXPIRE_MINUTES} minutes</strong>.</p>
                <p>If you didn't create an account with Credlyse, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>© 2026 Credlyse. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_verification_email_text(otp_code: str, full_name: str) -> str:
    """Generate plain text content for verification email."""
    return f"""
Hi {full_name},

Welcome to Credlyse! Please use the verification code below to complete your registration:

Your verification code: {otp_code}

This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.

If you didn't create an account with Credlyse, you can safely ignore this email.

© 2026 Credlyse. All rights reserved.
    """


async def send_verification_email(
    to_email: str,
    otp_code: str,
    full_name: str,
) -> bool:
    """
    Send email verification OTP.
    
    Args:
        to_email: Recipient email address.
        otp_code: The OTP code to send.
        full_name: User's full name for personalization.
        
    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    # In development mode, just log the OTP
    if settings.is_development and not settings.SMTP_USER:
        logger.info(f"[DEV MODE] OTP for {to_email}: {otp_code}")
        print(f"\n{'='*50}")
        print(f"📧 DEVELOPMENT MODE - Email OTP")
        print(f"To: {to_email}")
        print(f"OTP Code: {otp_code}")
        print(f"{'='*50}\n")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Verify your Credlyse account - {otp_code}"
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
        msg["To"] = to_email
        
        # Attach plain text and HTML versions
        text_part = MIMEText(get_verification_email_text(otp_code, full_name), "plain")
        html_part = MIMEText(get_verification_email_html(otp_code, full_name), "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.EMAIL_FROM_ADDRESS,
                to_email,
                msg.as_string()
            )
        
        logger.info(f"Verification email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {to_email}: {e}")
        return False


def get_password_reset_email_html(otp_code: str, full_name: str) -> str:
    """Generate HTML content for password reset email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); padding: 40px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px; }}
            .otp-box {{ background: #f3f4f6; border: 2px dashed #d1d5db; border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0; }}
            .otp-code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #6d28d9; font-family: monospace; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
            p {{ color: #374151; line-height: 1.6; }}
            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 20px 0; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Password Reset</h1>
            </div>
            <div class="content">
                <p>Hi {full_name},</p>
                <p>We received a request to reset your Credlyse password. Use the code below to reset it:</p>
                
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                
                <p>This code will expire in <strong>{settings.OTP_EXPIRE_MINUTES} minutes</strong>.</p>
                
                <div class="warning">
                    <strong>⚠️ Didn't request this?</strong><br>
                    If you didn't request a password reset, please ignore this email. Your account is still secure.
                </div>
            </div>
            <div class="footer">
                <p>© 2026 Credlyse. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_password_reset_email_text(otp_code: str, full_name: str) -> str:
    """Generate plain text content for password reset email."""
    return f"""
Hi {full_name},

We received a request to reset your Credlyse password. Use the code below to reset it:

Your reset code: {otp_code}

This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.

If you didn't request a password reset, please ignore this email. Your account is still secure.

© 2026 Credlyse. All rights reserved.
    """


async def send_password_reset_email(
    to_email: str,
    otp_code: str,
    full_name: str,
) -> bool:
    """
    Send password reset OTP.
    
    Args:
        to_email: Recipient email address.
        otp_code: The OTP code to send.
        full_name: User's full name for personalization.
        
    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    # In development mode, just log the OTP
    if settings.is_development and not settings.SMTP_USER:
        logger.info(f"[DEV MODE] Password reset OTP for {to_email}: {otp_code}")
        print(f"\n{'='*50}")
        print(f"🔐 DEVELOPMENT MODE - Password Reset OTP")
        print(f"To: {to_email}")
        print(f"OTP Code: {otp_code}")
        print(f"{'='*50}\n")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Reset your Credlyse password - {otp_code}"
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
        msg["To"] = to_email
        
        # Attach plain text and HTML versions
        text_part = MIMEText(get_password_reset_email_text(otp_code, full_name), "plain")
        html_part = MIMEText(get_password_reset_email_html(otp_code, full_name), "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.EMAIL_FROM_ADDRESS,
                to_email,
                msg.as_string()
            )
        
        logger.info(f"Password reset email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        return False

