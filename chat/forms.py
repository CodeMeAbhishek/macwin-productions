from django import forms
from django.contrib.auth.models import User
from .models import Profile, Post, Comment

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'relationship_status', 'year', 'branch', 'bio', 'profile_pic']
        widgets = {
            'year': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'placeholder': 'Enter your college year (1-5)'
            })
        }

class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'relationship_status', 'year', 'branch', 'bio', 'profile_pic']
        widgets = {
            'year': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'placeholder': 'Enter your college year (1-5)'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us about yourself! Share your interests, hobbies, or anything you\'d like others to know.'
            })
        }
        help_texts = {
            'bio': 'Your bio will be displayed on your profile page and helps others get to know you better.'
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What\'s on your mind?'
            }),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': 'Write a comment...'}),
        }

class RegistrationForm(forms.Form):
    email = forms.EmailField()
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

class OTPVerificationForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    otp = forms.CharField(label="Enter OTP")