from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        
        # Update profile if needed
        if hasattr(user, 'profile'):
            email = sociallogin.account.extra_data.get('email')
            name = sociallogin.account.extra_data.get('name', '')
            user.profile.email = email
            user.profile.full_name = name
            user.profile.is_email_verified = True
            user.profile.save()
        
        return user