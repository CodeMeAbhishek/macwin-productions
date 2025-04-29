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
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Enter your full name',
                'class': 'form-control'
            }),
            'year': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'placeholder': 'Enter your college year (1-5)',
                'class': 'form-control'
            }),
            'branch': forms.TextInput(attrs={
                'placeholder': 'Enter your branch/department',
                'class': 'form-control'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us about yourself! Share your interests, hobbies, or anything you\'d like others to know.',
                'class': 'form-control'
            }),
            'relationship_status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        help_texts = {
            'full_name': 'Your full name as you want it to appear on your profile.',
            'year': 'Your current year of study (1-5).',
            'branch': 'Your branch or department of study.',
            'bio': 'Your bio will be displayed on your profile page and helps others get to know you better.',
            'profile_pic': 'Upload a profile picture (optional).',
            'relationship_status': 'Your current relationship status (optional).'
        }
        
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        return full_name

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

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content.strip():
            raise forms.ValidationError("Post content cannot be empty.")
        if len(content) > 1000:
            raise forms.ValidationError("Post content cannot exceed 1000 characters.")
        return content

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5*1024*1024:  # 5MB
                raise forms.ValidationError("Image size should not exceed 5MB")
            if not image.content_type in ['image/jpeg', 'image/png']:
                raise forms.ValidationError("Only JPEG and PNG images are allowed")
        return image

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