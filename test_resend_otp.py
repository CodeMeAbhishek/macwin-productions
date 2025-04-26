import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.utils import send_otp_email

def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

if __name__ == '__main__':
    email = 'gupta.b.abhishek@nuv.ac.in'
    otp = generate_otp()
    print(f'Sending OTP {otp} to {email}...')
    success = send_otp_email(email, otp)
    if success:
        print('OTP email sent successfully!')
    else:
        print('Failed to send OTP email.') 