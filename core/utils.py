import resend
from django.conf import settings

def send_otp_email(email, otp):
    """
    Send OTP email using Resend API
    """
    try:
        resend.api_key = settings.RESEND_API_KEY
        
        resend.Emails.send({
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
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False 