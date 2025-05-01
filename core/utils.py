import resend
from django.conf import settings
import random
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp):
    """
    Send OTP email using Resend API
    
    Args:
        email (str): Recipient email address
        otp (str): One-time password to send
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    Raises:
        ValueError: If email or OTP is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Invalid email address")
    if not otp or not isinstance(otp, str):
        raise ValueError("Invalid OTP")
        
    try:
        if not settings.RESEND_API_KEY:
            logger.error("RESEND_API_KEY not configured")
            return False
            
        resend.api_key = settings.RESEND_API_KEY
        
        response = resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": email,
            "subject": "Your OTP Code",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Your OTP Code</h2>
                    <p>Your One-Time Password (OTP) is:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px;">{otp}</span>
                    </div>
                    <p>This OTP is valid for a limited time. Please do not share it with anyone.</p>
                    <p style="color: #666; font-size: 12px; margin-top: 20px;">If you didn't request this OTP, please ignore this email.</p>
                </div>
            """
        })
        
        if response and getattr(response, 'id', None):
            logger.info(f"Email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send email to {email}: No response ID")
            return False
            
    except resend.ApiError as e:
        logger.error(f"Resend API error sending email to {email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {email}: {str(e)}")
        return False

def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)]) 