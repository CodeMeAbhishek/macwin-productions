import os
import django
from django.core.mail import send_mail

# Set Outlook SMTP credentials directly for testing
os.environ['EMAIL_HOST_USER'] = 'shyinenuv@outlook.com'
os.environ['EMAIL_HOST_PASSWORD'] = 'elhmbcjkbpfdbnnd'
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