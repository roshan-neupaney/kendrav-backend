# authentication/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication, AuthenticationFailed
from users.models import UserToken
from django.utils import timezone

User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return result
        
        user, token = result

        device_id = request.headers.get('deviceId', '')

        if not device_id:
            raise AuthenticationFailed('Device Id is required')
        
        UserToken.objects.filter(user=user, device_id=device_id, is_active=True).update(last_active_at=timezone.now())
        
        return user, token