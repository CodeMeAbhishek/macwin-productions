from django.db.models import Q
from .models import FriendRequest, Message
from django.core.mail import send_mail
import random
from django.conf import settings

def get_user_friends(user):
    """Get all friends of a user."""
    sent_requests = FriendRequest.objects.filter(from_user=user, is_accepted=True)
    received_requests = FriendRequest.objects.filter(to_user=user, is_accepted=True)
    friends = [req.to_user for req in sent_requests] + [req.from_user for req in received_requests]
    return friends

def get_friends_with_unread_messages(user):
    """Get friends with their unread message counts and last messages."""
    friends = get_user_friends(user)
    friends_data = []
    
    for friend in friends:
        unread_count = Message.objects.filter(
            sender=friend,
            receiver=user,
            is_read=False
        ).count()

        last_message = Message.objects.filter(
            Q(sender=user, receiver=friend) |
            Q(sender=friend, receiver=user)
        ).order_by('-timestamp').first()

        friends_data.append({
            'user': friend,
            'unread': unread_count,
            'last_message': last_message
        })
    
    return friends_data 

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(email, otp):
    subject = 'Verify your email - MacWin'
    message = f'Your OTP for email verification is: {otp}\n\nThis OTP will expire in 10 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        print(f"Attempting to send email to {email}")
        send_mail(subject, message, from_email, recipient_list)
        print(f"Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False