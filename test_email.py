import os
import django
from django.core.mail import send_mail

# Set Outlook SMTP credentials directly for testing
os.environ['EMAIL_HOST_USER'] = 'shyinenuv@outlook.com'  # Keep or load from env as well if needed
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
if not EMAIL_HOST_PASSWORD:
    raise ValueError("EMAIL_HOST_PASSWORD environment variable not set")
os.environ['EMAIL_HOST_PASSWORD'] = EMAIL_HOST_PASSWORD  # Set it for Django's mail functions if they read from environ directly

os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

django.setup()

try:
    result = send_mail(
        'Test Subject',
        'Test message body',
        'shyinenuv@outlook.com',
        ['shyinenuv@outlook.com'],
        fail_silently=False,
    )
    print(f"Email sent successfully! Result: {result}")
except Exception as e:
    print(f"Error sending email: {str(e)}")