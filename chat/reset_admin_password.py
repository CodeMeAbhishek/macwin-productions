import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("PYTHONPATH:", sys.path)
print("Current working directory:", os.getcwd())
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not username or not password:
    print("Please set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD environment variables.")
else:
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Password for superuser '{username}' has been reset and privileges ensured.")
    except User.DoesNotExist:
        print(f"Superuser '{username}' does not exist.") 