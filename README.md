# Application Screenshots

![Unisphere main feed showing user posts and interactions.](Screenshots/Screenshot%202025-06-15%20210402.png "Unisphere Main Feed")
_Unisphere main feed showing user posts and interactions._

![User profile page in Unisphere.](Screenshots/Screenshot%202025-06-15%20210509.png "User Profile")
_User profile page in Unisphere._

![Real-time chat interface.](Screenshots/Screenshot%202025-06-15%20210519.png "Chat Interface")
_Real-time chat interface._

# Unisphere - Social Media Platform

## Project Overview
Unisphere is a Django-based social media platform that provides features similar to popular social networks, including user profiles, friend connections, real-time chat, posts, likes, comments, and notifications.

## Core Files

### 1. settings.py
```python
# Main configuration file for the Django project
- Database configuration using dj_database_url
- Security settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Installed apps including Django, Channels, and third-party apps
- Middleware configuration
- Template settings
- Static and media file handling
- Email configuration
- WebSocket (Channels) configuration
- Security headers and SSL settings
- Cloudinary configuration for media storage
```

### 2. urls.py
```python
# Main URL routing configuration
- Root URL patterns
- Includes chat app URLs
- Admin interface URL
```

### 3. asgi.py
```python
# ASGI configuration for WebSocket support
- Django ASGI application setup
- Protocol type routing
- WebSocket support configuration
```

### 4. wsgi.py
```python
# WSGI configuration for HTTP requests
- Django WSGI application setup
- Standard WSGI application configuration
```

### 5. utils.py
```python
# Utility functions
- OTP generation
- Email sending functionality
- Helper functions for the application
```

## Chat Application Files

### 1. models.py
```python
# Database models for the chat application
class Profile:
    # User profile model with:
    - One-to-one relationship with User
    - Fields: full_name, branch, year, bio, profile_pic
    - Validation for file size and image format
    - Relationship status choices

class FriendRequest:
    # Friend request management
    - Tracks friend requests between users
    - Prevents self-friending
    - Handles request acceptance/decline

class Message:
    # Real-time messaging model
    - Sender and receiver relationships
    - Message content and timestamp
    - Read/unread status
    - Database indexes for performance

class Post:
    # Social media posts
    - User relationship
    - Content and image fields
    - Timestamp ordering

class Like:
    # Post likes
    - User and post relationships
    - Prevents duplicate likes
    - Timestamp tracking

class Comment:
    # Post comments
    - Post and user relationships
    - Content and timestamp

class Notification:
    # System notifications
    - Different notification types
    - Read/unread status
    - Timestamp ordering

class EmailVerification:
    # Email verification system
    - OTP storage
    - Expiration handling
```

### 2. views.py
```python
# View functions for handling HTTP requests
def index_view:
    # Main feed view
    - Post creation
    - Post listing
    - Like/comment handling

def register_view:
    # User registration
    - Form handling
    - Email verification
    - OTP generation

def login_view:
    # User authentication
    - Credential validation
    - Session management

def profile_view:
    # Profile management
    - Profile editing
    - Friend list display

def chat_with_friend:
    # Chat interface
    - Message history
    - Real-time updates

def notifications_view:
    # Notification management
    - Notification listing
    - Mark as read functionality
```

### 3. consumers.py
```python
# WebSocket handling for real-time features
class ChatConsumer:
    # Handles WebSocket connections
    async def connect:
        # Establishes WebSocket connection
        - Room creation
        - Channel layer setup

    async def disconnect:
        # Handles connection closure
        - Cleanup of resources

    async def receive:
        # Message processing
        - Message validation
        - Type handling
        - Error management

    async def handle_chat_message:
        # Chat message processing
        - Message saving
        - Broadcast to room
        - Error handling

    async def handle_read_receipt:
        # Read receipt handling
        - Message status updates
        - Broadcast to users
```

### 4. forms.py
```python
# Form definitions for data validation
class RegisterForm:
    # User registration form
    - Username validation
    - Password requirements
    - Email validation

class ProfileForm:
    # Profile editing form
    - Profile field validation
    - Image upload handling

class PostForm:
    # Post creation form
    - Content validation
    - Image upload handling

class CommentForm:
    # Comment creation form
    - Content validation
    - Post relationship
```

### 5. routing.py
```python
# WebSocket routing configuration
- URL patterns for WebSocket connections
- Consumer mapping
```

### 6. urls.py
```python
# URL patterns for the chat application
- View function mappings
- Path configurations
- Name spacing
```

### 7. context_processors.py
```python
# Template context processors
- Notification count
- User status
- Global template variables
```

### 8. admin.py
```python
# Admin interface configuration
- Model registration
- Admin customization
```

### 9. apps.py
```python
# Chat application configuration
- App name
- Default configuration
```

### 10. tests.py
```python
# Test cases
- Basic test setup
- Test configuration
```

## Templates

### Base Templates
1. **base.html**
   - Main layout template
   - Navigation bar
   - Footer
   - Common CSS/JS includes
   - Responsive design

### Authentication Templates
1. **login.html**
   - User login form
   - Error handling
   - Remember me option

2. **register.html**
   - User registration form
   - Email validation
   - Password requirements

3. **verify_otp.html**
   - OTP verification interface
   - Countdown timer
   - Resend OTP option

### Profile Templates
1. **profile.html**
   - User profile display
   - Profile editing form
   - Profile picture upload

2. **complete_profile.html**
   - Initial profile setup
   - Required information collection
   - Profile picture upload

3. **user_profile.html**
   - Other users' profile view
   - Friend request button
   - User posts display

### Social Features Templates
1. **index.html**
   - Main feed
   - Post creation form
   - Posts display
   - Like/comment functionality

2. **friends.html**
   - Friends list
   - Friend requests
   - Friend search

3. **find_friends.html**
   - User search interface
   - Search results display
   - Add friend functionality

### Messaging Templates
1. **messages.html**
   - Chat list
   - Unread message indicators
   - Message previews

2. **chat_room.html**
   - Real-time chat interface
   - Message history
   - Message input
   - Read receipts

### Notification Templates
1. **notifications.html**
   - Notification list
   - Notification types
   - Mark as read functionality
   - Clear all option

### Admin Templates
1. **admin_dashboard.html**
   - User management
   - Content moderation
   - System statistics

### Information Templates
1. **about.html**
   - Platform information
   - Team details
   - Mission statement

2. **faq.html**
   - Frequently asked questions
   - Help documentation

3. **terms.html**
   - Terms of service
   - User agreements

4. **privacy.html**
   - Privacy policy
   - Data handling

5. **contact.html**
   - Contact form
   - Support information

### Partial Templates
1. **post_card.html**
   - Post display component
   - Like/comment buttons
   - Post actions

2. **comment_section.html**
   - Comments display
   - Comment form
   - Reply functionality

## Technical Stack
- **Backend**: Django 5.2
- **Real-time**: Django Channels
- **Database**: SQLite/PostgreSQL
- **Media Storage**: Cloudinary
- **WebSocket**: Redis/InMemory
- **Email**: Resend API
- **Static Files**: WhiteNoise

## Features
1. **User Management**
   - Secure registration with email verification
   - Profile customization
   - Privacy settings

2. **Social Interaction**
   - Friend system
   - Post creation and sharing
   - Like and comment functionality
   - Real-time notifications

3. **Messaging**
   - Real-time chat
   - Read receipts
   - Message history
   - File sharing

4. **Content Management**
   - Post creation and editing
   - Media upload
   - Comment system
   - Content moderation

## Security
- Email verification
- Secure authentication
- File validation
- CSRF protection
- SSL enforcement
- XSS protection

## Database
- Optimized queries
- Proper indexing
- Efficient relationships
- Transaction management

## File Management
- Cloudinary integration
- File size validation
- Image format validation
- Static file optimization