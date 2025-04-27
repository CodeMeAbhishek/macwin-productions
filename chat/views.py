from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm, ProfileForm, ProfileCompletionForm, PostForm, CommentForm, RegistrationForm, OTPVerificationForm
from .models import Profile, Post, Like, Comment, Notification, EmailVerification
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import FriendRequest, Message
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from core.utils import generate_otp, send_otp_email
import json
from django.utils.dateparse import parse_datetime

def unread_notifications_count(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications': request.user.notifications.filter(is_read=False).count()
        }
    return {'unread_notifications': 0}

@login_required
def index_view(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if content or image:
            post = Post.objects.create(
                user=request.user,
                content=content,
                image=image
            )
            
            # If it's an AJAX request, return the rendered post
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                post.likes_count = post.likes.count()
                post.comments_count = post.comments.count()
                post.is_liked = False
                return JsonResponse({
                    'status': 'success',
                    'html': render_to_string('chat/partials/post_card.html', {'post': post}, request=request)
                })
            
            return redirect('index')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'error': 'Content or image is required'
                }, status=400)
            
            messages.error(request, 'Content or image is required')
            return redirect('index')

    # Get all posts ordered by timestamp (newest first)
    posts = Post.objects.select_related('user__profile').prefetch_related('comments', 'likes').order_by('-timestamp')
    
    # Annotate posts with additional information
    for post in posts:
        post.likes_count = post.likes.count()
        post.comments_count = post.comments.count()
        post.is_liked = post.likes.filter(user=request.user).exists()

    # Get unread notifications count
    unread_notifications = request.user.notifications.filter(is_read=False).count()

    context = {
        'posts': posts,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'chat/index.html', context)

def handle_post_request(request):
    if 'comment_content' in request.POST:
        return handle_comment(request)
    else:
        return handle_post_creation(request)

def handle_comment(request):
    post_id = request.POST.get('post_id')
    post = Post.objects.get(id=post_id)
    comment = Comment.objects.create(
        user=request.user,
        post=post,
        content=request.POST.get('comment_content')
    )
    if post.user != request.user:
        Notification.objects.create(
            user=post.user,
            sender=request.user,
            notif_type='comment',
            message=f"{request.user.username} commented on your post.",
            post=post
        )
    return redirect('index')

def handle_post_creation(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
    return redirect('index')

def handle_search(query, current_user):
    return User.objects.filter(
        Q(username__icontains=query) | Q(profile__full_name__icontains=query)
    ).exclude(id=current_user.id)

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            allowed_domains = ['nuv.ac.in', 'gmail.com', 'outlook.com']
            email_domain = email.split('@')[-1]
            if email_domain not in allowed_domains:
                form.add_error('email', 'Registration is only allowed for @nuv.ac.in, @gmail.com, or @outlook.com email addresses.')
            elif User.objects.filter(email=email).exists():
                form.add_error('email', 'This email is already registered.')
            elif User.objects.filter(username=username).exists():
                form.add_error('username', 'Username already taken.')
            else:
                otp = generate_otp()
                EmailVerification.objects.update_or_create(
                    email=email, defaults={'otp': otp}
                )
                send_otp_email(email, otp)
                request.session['pending_email'] = email
                request.session['pending_username'] = username
                request.session['pending_password'] = password
                request.session['otp_created_at'] = timezone.now().isoformat()
                return redirect('verify_otp')
    else:
        form = RegistrationForm()
    return render(request, 'chat/register.html', {'form': form})

def verify_otp_view(request):
    email = request.session.get('pending_email')
    if not email:
        return redirect('register')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST, initial={'email': email})
        if form.is_valid():
            otp_input = form.cleaned_otp
            try:
                record = EmailVerification.objects.get(email=email)
                if record.is_expired():
                    form.add_error(None, "OTP expired. Please register again.")
                    record.delete()
                elif record.otp != otp_input:
                    form.add_error('otp', "Invalid OTP")
                else:
                    # Create user now
                    username = request.session['pending_username']
                    password = request.session['pending_password']
                    user = User.objects.create_user(
                        username=username, email=email, password=password
                    )
                    EmailVerification.objects.filter(email=email).delete()
                    request.session.flush()
                    messages.success(request, "Email verified. Please login.")
                    return redirect('login')
            except EmailVerification.DoesNotExist:
                form.add_error(None, "Verification record not found.")
    else:
        form = OTPVerificationForm(initial={'email': email})
    
    # Calculate seconds remaining for the timer
    otp_created_at = request.session.get('otp_created_at')
    if otp_created_at:
        created_at = parse_datetime(otp_created_at)
    else:
        try:
            record = EmailVerification.objects.get(email=email)
            created_at = record.created_at
        except EmailVerification.DoesNotExist:
            created_at = None

    if created_at:
        time_left = (created_at + timedelta(minutes=3)) - timezone.now()
        seconds_remaining = max(int(time_left.total_seconds()), 0)
    else:
        seconds_remaining = 0
    
    return render(request, 'chat/verify_otp.html', {
        'form': form,
        'seconds_remaining': seconds_remaining
    })

def login_view(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=uname, password=pwd)

        if user is not None:
            login(request, user)
            # Check if user has a profile
            try:
                user.profile
                return redirect('index')
            except Profile.DoesNotExist:
                return redirect('complete_profile', user_id=user.id)
        else:
            messages.error(request, "Invalid Credentials.")
    return render(request, 'chat/login.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return redirect('complete_profile', user_id=request.user.id)
        
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
    else:
        form = ProfileForm(instance=profile)
    
    # Get user's friends
    friends = get_user_friends(request.user)
    
    return render(request, 'chat/profile.html', {
        'form': form,
        'friends': friends
    })

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def send_friend_request(request, user_id):
    """Send a friend request to another user."""
    try:
        to_user = User.objects.get(id=user_id)
        if request.user != to_user:
            friend_request, created = FriendRequest.objects.get_or_create(
                from_user=request.user, 
                to_user=to_user
            )
            if created:
                # Create notification for friend request
                Notification.objects.create(
                    user=to_user,
                    sender=request.user,
                    notif_type='friend_request',
                    message=f"{request.user.username} sent you a friend request."
                )
                return JsonResponse({'status': 'success', 'message': 'Friend request sent'})
            else:
                return JsonResponse(
                    {'status': 'error', 'error': 'Friend request already sent'}, 
                    status=400
                )
        else:
            return JsonResponse(
                {'status': 'error', 'error': 'You cannot send a friend request to yourself'}, 
                status=400
            )
    except User.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'error': 'User not found'}, 
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'error': str(e)}, 
            status=500
        )

@login_required
def cancel_friend_request(request, user_id):
    try:
        to_user = User.objects.get(id=user_id)
        FriendRequest.objects.filter(from_user=request.user, to_user=to_user).delete()
        return JsonResponse({'status': 'success', 'message': 'Friend request cancelled'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

@login_required
def accept_friend_request(request, request_id):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'error': 'Method not allowed'
        }, status=405)
        
    try:
        # Get the notification first
        notification = get_object_or_404(Notification, id=request_id, user=request.user)
        
        # Find and accept the friend request
        friend_request = FriendRequest.objects.get(
            from_user=notification.sender,
            to_user=request.user,
            is_accepted=False
        )
        
        # Accept the request
        friend_request.is_accepted = True
        friend_request.save()
        
        # Delete any duplicate requests in the opposite direction
        FriendRequest.objects.filter(
            from_user=request.user,
            to_user=notification.sender
        ).delete()
        
        # Delete the notification instead of marking it as read
        notification.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Friend request accepted',
            'friend_id': notification.sender.id,
            'friend_name': notification.sender.profile.full_name
        })
        
    except (Notification.DoesNotExist, FriendRequest.DoesNotExist) as e:
        return JsonResponse({
            'status': 'error',
            'error': 'Friend request not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

@login_required
def decline_friend_request(request, request_id):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'error': 'Method not allowed'
        }, status=405)
        
    try:
        # Get the notification first
        notification = get_object_or_404(Notification, id=request_id, user=request.user)
        
        # Find and delete the friend request
        friend_request = FriendRequest.objects.get(
            from_user=notification.sender,
            to_user=request.user,
            is_accepted=False
        )
        
        # Delete the friend request
        friend_request.delete()
        
        # Mark notification as read
        notification.is_read = True
        notification.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Friend request declined'
        })
        
    except (Notification.DoesNotExist, FriendRequest.DoesNotExist) as e:
        return JsonResponse({
            'status': 'error',
            'error': 'Friend request not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

@login_required
def friends_list_view(request):
    friends_data = get_friends_with_unread_messages(request.user)
    return render(request, 'chat/friends.html', {'friends': friends_data})


@login_required
def find_friends_view(request):
    query = request.GET.get('q')
    
    # Get IDs of existing friends
    friends_ids = FriendRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)),
        is_accepted=True
    ).values_list('from_user', 'to_user')
    
    # Flatten and uniquify friend IDs
    friends_set = set()
    for from_id, to_id in friends_ids:
        friends_set.add(from_id)
        friends_set.add(to_id)
    friends_set.discard(request.user.id)  # Remove self from set
    
    # Base query excluding friends and self
    base_query = User.objects.exclude(
        id__in=list(friends_set)
    ).exclude(id=request.user.id)
    
    if query:
        # Search with query
        results = base_query.filter(
            Q(username__icontains=query) | 
            Q(profile__full_name__icontains=query)
        )
    else:
        # Get random selection when no query
        results = base_query.order_by('?')[:10]
    
    # Add friend request status for each user
    for user in results:
        user.friend_request_sent = FriendRequest.objects.filter(
            from_user=request.user,
            to_user=user,
            is_accepted=False
        ).exists()
        user.friend_request_received = FriendRequest.objects.filter(
            from_user=user,
            to_user=request.user,
            is_accepted=False
        ).exists()

    return render(request, 'chat/find_friends.html', {
        'results': results,
        'query': query
    })

def get_user_friends(user):
    # Get all accepted friend requests where user is either sender or receiver
    sent_requests = FriendRequest.objects.filter(from_user=user, is_accepted=True)
    received_requests = FriendRequest.objects.filter(to_user=user, is_accepted=True)
    
    # Combine friends from both sent and received requests
    friends = [req.to_user for req in sent_requests] + [req.from_user for req in received_requests]
    return friends

@login_required
def user_profile_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Get user's friends
    user_friends = get_user_friends(other_user)
    
    # Check friendship status
    is_friend = FriendRequest.objects.filter(
        (Q(from_user=request.user, to_user=other_user) |
        Q(from_user=other_user, to_user=request.user)),
        is_accepted=True
    ).exists()

    friend_request_sent = FriendRequest.objects.filter(
        from_user=request.user, 
        to_user=other_user, 
        is_accepted=False
    ).first()

    friend_request_received = FriendRequest.objects.filter(
        from_user=other_user, 
        to_user=request.user, 
        is_accepted=False
    ).first()

    context = {
        'other_user': other_user,
        'profile': other_user.profile,
        'friends': user_friends,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent is not None,
        'friend_request_received': friend_request_received is not None,
        'friend_request': friend_request_received,
    }

    return render(request, 'chat/user_profile.html', context)

@login_required
def chat_with_friend(request, friend_id):
    try:
        friend = get_object_or_404(User, id=friend_id)
        print(f"Found friend with ID {friend_id}: {friend.username}")

        # Ensure they're friends
        is_friend = FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=friend) |
            Q(from_user=friend, to_user=request.user),
            is_accepted=True
        ).exists()
        
        print(f"Friendship status with {friend.username}: {is_friend}")

        if not is_friend:
            print(f"No friendship found between {request.user.username} and {friend.username}")
            messages.error(request, "You are not friends with this user.")
            return redirect('friends')

        # Get chat history
        messages_qs = Message.objects.filter(
            Q(sender=request.user, receiver=friend) |
            Q(sender=friend, receiver=request.user)
        ).order_by('timestamp')

        print(f"Found {messages_qs.count()} messages in chat history")

        # Create a unique room name based on user IDs
        room_name = f"{min(request.user.id, friend.id)}_{max(request.user.id, friend.id)}"

        # Mark unread messages as read
        unread_count = Message.objects.filter(sender=friend, receiver=request.user, is_read=False).update(is_read=True)
        print(f"Marked {unread_count} messages as read")

        return render(request, 'chat/chat_room.html', {
            'friend': friend,
            'chat_messages': messages_qs,
            'room_name': room_name
        })
    except Exception as e:
        print(f"Error in chat_with_friend: {str(e)}")
        messages.error(request, "An error occurred while loading the chat. Please try again.")
        return redirect('messages')

def complete_profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # If user already has a profile, redirect to index
    try:
        user.profile
        return redirect('index')
    except Profile.DoesNotExist:
        pass
        
    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Log the user in if they're not already logged in
            if not request.user.is_authenticated:
                login(request, user)
            
            messages.success(request, "Profile completed successfully!")
            return redirect('index')
    else:
        form = ProfileCompletionForm()
    return render(request, 'chat/complete_profile.html', {'form': form})

@login_required
def like_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
        
    try:
        post = Post.objects.get(id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            # User already liked the post, so unlike it
            like.delete()
            return JsonResponse({
                'status': 'success',
                'action': 'unliked',
                'likes_count': post.likes.count()
            })
        else:
            # Create notification for the post owner if it's not the same user
            if post.user != request.user:
                Notification.objects.create(
                    user=post.user,
                    sender=request.user,
                    notif_type='like',
                    message=f"liked your post",
                    post=post
                )
            
            return JsonResponse({
                'status': 'success',
                'action': 'liked',
                'likes_count': post.likes.count()
            })
            
    except Post.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Post not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)

    if request.method == 'POST':
        new_content = request.POST.get('content')
        post.content = new_content
        post.save()
        return redirect('index')

    return render(request, 'chat/edit_post.html', {'post': post})

@login_required
def delete_post(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id, user=request.user)
        post.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Post deleted successfully'
            })
        return redirect('index')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        messages.error(request, str(e))
        return redirect('index')

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return redirect('index')

@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-timestamp')
    unread_count = notifs.filter(is_read=False).count()

    # If it's an AJAX call, mark all as read
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        notifs.update(is_read=True)
        html = render_to_string('chat/partials/notification_list.html', {'notifications': notifs})
        return JsonResponse({'html': html, 'unread_count': 0})

    return render(request, 'chat/notifications.html', {'notifications': notifs})

# Static pages
class AboutView(TemplateView):
    template_name = 'chat/about.html'

class FAQView(TemplateView):
    template_name = 'chat/faq.html'

class TermsView(TemplateView):
    template_name = 'chat/terms.html'

class PrivacyView(TemplateView):
    template_name = 'chat/privacy.html'

@csrf_exempt
def contact_view(request):
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Optional: send email (or store in DB/log)
        print(f"Message from {name} ({email}): {message}")
        success = True
    return render(request, 'chat/contact.html', {'success': success})

@staff_member_required
def admin_dashboard(request):
    users = User.objects.all()
    posts = Post.objects.select_related('user').order_by('-timestamp')
    
    # Basic counts
    total_users = users.count()
    total_posts = posts.count()
    total_comments = Comment.objects.count()
    active_users = users.filter(is_active=True).count()
    blocked_users = total_users - active_users

    # Posts this week (last 7 days)
    today = timezone.now()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    posts_per_day = []
    for day in last_7_days:
        count = Post.objects.filter(
            timestamp__date=day.date()
        ).count()
        posts_per_day.append({'date': day.strftime("%b %d"), 'count': count})

    context = {
        'users': users,
        'posts': posts,
        'total_users': total_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'active_users': active_users,
        'blocked_users': blocked_users,
        'posts_per_day': posts_per_day,
    }
    return render(request, 'chat/admin_dashboard.html', context)

@require_POST
@staff_member_required
def toggle_block_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('admin_dashboard')

@require_POST
@staff_member_required
def delete_post_admin(request, post_id):
    post = Post.objects.get(id=post_id)
    post.delete()
    return redirect('admin_dashboard')

@login_required
@require_POST
def delete_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('notifications')

@login_required
def messages_view(request):
    """View all messages across all conversations."""
    friends_with_messages = get_friends_with_unread_messages(request.user)
    
    # Sort friends by last message timestamp, most recent first
    friends_with_messages.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(),
        reverse=True
    )
    
    return render(request, 'chat/messages.html', {
        'friends_with_messages': friends_with_messages
    })

@login_required
def account_view(request):
    """View and manage account settings."""
    if request.method == 'POST':
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password == confirm_password:
            user = authenticate(username=request.user.username, password=current_password)
            if user is not None:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated successfully!")
                login(request, user)  # Re-login the user
            else:
                messages.error(request, "Current password is incorrect.")
        else:
            messages.error(request, "New passwords don't match.")
    
    return render(request, 'chat/account.html')

@login_required
def privacy_view(request):
    """View and manage privacy settings."""
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update privacy settings
        profile.relationship_status = request.POST.get('relationship_status', '')
        profile.save()
        messages.success(request, "Privacy settings updated!")
    
    return render(request, 'chat/privacy.html', {
        'profile': profile
    })

@login_required
def remove_friend(request, user_id):
    try:
        friend = get_object_or_404(User, id=user_id)
        FriendRequest.objects.filter(
            (Q(from_user=request.user, to_user=friend) |
             Q(from_user=friend, to_user=request.user)),
            is_accepted=True
        ).delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Removed {friend.profile.full_name} from your friends'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

@login_required
def add_comment(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
        
    try:
        post = Post.objects.get(id=post_id)
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'status': 'error',
                'error': 'Comment content is required'
            }, status=400)
            
        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=content
        )
        
        # Create notification for post owner if it's not the same user
        if post.user != request.user:
            Notification.objects.create(
                user=post.user,
                sender=request.user,
                notif_type='comment',
                message=f"commented on your post",
                post=post
            )
        
        # Render the new comment HTML
        comment_html = render_to_string(
            'chat/partials/comment.html',
            {'comment': comment},
            request=request
        )
        
        return JsonResponse({
            'status': 'success',
            'html': comment_html,
            'comments_count': post.comments.count()
        })
        
    except Post.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Post not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

@login_required
def delete_comment(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Method not allowed'}, status=405)
        
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
        post = comment.post
        comment.delete()
        
        return JsonResponse({
            'status': 'success',
            'comments_count': post.comments.count()
        })
        
    except Comment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Comment not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=400)

@login_required
def clear_all_notifications(request):
    if request.method == 'POST':
        try:
            # Delete all notifications for the current user
            request.user.notifications.all().delete()
            return JsonResponse({
                'status': 'success',
                'message': 'All notifications cleared'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@require_POST
def resend_otp_view(request):
    email = request.session.get('pending_email')
    if not email:
        return JsonResponse({'error': 'No session'}, status=400)
    
    otp = generate_otp()
    EmailVerification.objects.update_or_create(
        email=email, 
        defaults={'otp': otp, 'created_at': timezone.now()}
    )
    send_otp_email(email, otp)
    return JsonResponse({'status': 'resent'})

def get_friends_with_unread_messages(user):
    """
    Returns a list of friends with their unread message count and last message.
    """
    # Get all accepted friends
    sent_requests = FriendRequest.objects.filter(from_user=user, is_accepted=True)
    received_requests = FriendRequest.objects.filter(to_user=user, is_accepted=True)
    friends = [req.to_user for req in sent_requests] + [req.from_user for req in received_requests]

    friends_data = []
    for friend in friends:
        # Get unread messages from this friend to the user
        unread_count = Message.objects.filter(sender=friend, receiver=user, is_read=False).count()
        # Get the last message between user and friend
        last_message = Message.objects.filter(
            Q(sender=user, receiver=friend) | Q(sender=friend, receiver=user)
        ).order_by('-timestamp').first()
        friends_data.append({
            'user': friend,
            'unread_count': unread_count,
            'last_message': last_message,
        })
    return friends_data
