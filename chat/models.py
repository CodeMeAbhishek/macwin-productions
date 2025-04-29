from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import random
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q

class Profile(models.Model):
    RELATIONSHIP_CHOICES = [
        ('S', 'Single'),
        ('R', 'In a Relationship'),
        ('C', "It's complicated"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50, blank=True, default='')
    year = models.IntegerField(
        verbose_name='College Year',
        help_text='Enter a value between 1 and 5',
        validators=[
            MinValueValidator(1, message='College year must be at least 1'),
            MaxValueValidator(5, message='College year cannot be more than 5')
        ],
        default=1
    )
    bio = models.TextField(blank=True, default='')
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    relationship_status = models.CharField(max_length=1, choices=RELATIONSHIP_CHOICES, blank=True, default='')

    def clean(self):
        if not self.full_name.strip():
            raise ValidationError("Full name cannot be empty.")
        if len(self.full_name) > 100:
            raise ValidationError("Full name cannot exceed 100 characters.")
        if self.bio and len(self.bio) > 500:
            raise ValidationError("Bio cannot exceed 500 characters.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username
    
class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def clean(self):
        if self.from_user == self.to_user:
            raise ValidationError("You cannot send a friend request to yourself.")
        
        # Check for existing friendship
        if FriendRequest.objects.filter(
            (Q(from_user=self.from_user, to_user=self.to_user) |
             Q(from_user=self.to_user, to_user=self.from_user)),
            is_accepted=True
        ).exists():
            raise ValidationError("You are already friends with this user.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.from_user} → {self.to_user}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['timestamp']),
        ]

    def clean(self):
        if self.sender == self.receiver:
            raise ValidationError("You cannot send a message to yourself.")
        if len(self.content.strip()) == 0:
            raise ValidationError("Message content cannot be empty.")
        if len(self.content) > 1000:
            raise ValidationError("Message content cannot exceed 1000 characters.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.content[:30]}"

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']  # latest post first

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # Prevent duplicate likes

    def __str__(self):
        return f"{self.user.username} likes {self.post}"

class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on Post {self.post.id}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('friend_request', 'Friend Request'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey('Post', null=True, blank=True, on_delete=models.CASCADE)
    profile_user = models.ForeignKey(User, null=True, blank=True, related_name='linked_profile', on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sender.username} -> {self.user.username}: {self.message}"

class EmailVerification(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=3)