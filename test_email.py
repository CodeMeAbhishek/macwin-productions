import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unisphere.settings')
django.setup()

try:
    result = send_mail(
        'Test Subject',
        'Test message body',
        'official.riseaboveall@gmail.com',
        ['official.riseaboveall@gmail.com'],
        fail_silently=False,
    )
    print(f"Email sent successfully! Result: {result}")
except Exception as e:
    print(f"Error sending email: {str(e)}") 