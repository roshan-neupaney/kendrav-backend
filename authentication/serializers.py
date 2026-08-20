from users.models import UserToken
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
import secrets
from django.conf import settings
from .utils import send_otp_email, send_reset_link_email



User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False)
    device_id = serializers.CharField(write_only=True)
    device_name = serializers.CharField(write_only=True, required=False)
    location = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "full_name",
            "device_id",
            "device_name",
            "location",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")
        return email

    def create(self, validated_data):
        full_name = validated_data.pop("full_name", "")
        device_id = validated_data.pop("device_id")
        device_name = validated_data.pop("device_name", "")
        location = validated_data.pop("location", "")

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        if full_name and hasattr(user, "profile"):
            user.profile.full_name = full_name
            user.profile.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        UserToken.objects.create(
            user=user,
            refresh_token=refresh_token,
            device_id=device_id,
            device_name=device_name,
            location=location,
        )
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(write_only=True)
    device_name = serializers.CharField(write_only=True, required=False)
    location = serializers.CharField(write_only=True, required=False)

    def create(self, attrs):
        email = attrs.pop("email")
        password = attrs.pop("password")
        device_id = attrs.pop("device_id")
        device_name = attrs.pop("device_name", "")
        location = attrs.pop("location", "")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid Email")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect Password")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        user_old_tokens = UserToken.objects.filter(
            user=user, device_id=device_id, is_active=True
        )
        for token_data in user_old_tokens:
            try:
                old_refresh_token = RefreshToken(token_data.refresh_token)
                old_refresh_token.blacklist()
            except TokenError:
                pass
            token_data.is_active = False

        UserToken.objects.bulk_update(user_old_tokens, ["is_active"])

        UserToken.objects.create(
            user=user,
            refresh_token=refresh_token,
            location=location,
            device_id=device_id,
            device_name=device_name,
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    device_id = serializers.CharField(write_only=True)
    device_name = serializers.CharField(write_only=True, required=False)
    location = serializers.CharField(write_only=True, required=False)
    


class ActiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserToken
        fields = [
            "id",
            "user",
            "device_id",
            "device_name",
            "location",
            "is_active",
            "last_active_at",
            "created_at",
            "updated_at",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    old_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password = attrs.pop("new_password")
        old_password = attrs.pop("old_password")
        user = self.context.get("user")

        if not user.check_password(old_password):
            raise serializers.ValidationError("Old Password Is Incorrect")

        otp = str(random.randint(100000, 999999))
        hashed_password = make_password(new_password)

        cache.set(
            f"change_password:{user.id}", {"otp": otp, "new_password": hashed_password}, timeout=300
        )

        send_otp_email(user.email, otp)

        return {"message": 'Success'}


class ChangePasswordOTPSerializer(serializers.Serializer):
    otp_code = serializers.CharField(write_only=True)

    def validate(self, attrs):
        otp_code = attrs.pop("otp_code")
        user = self.context.get("user")

        attempts_key = f'change_password_attempts:{user.id}'
        attempts = cache.get(attempts_key, 0)

        change_password_data = cache.get(f"change_password:{user.id}", {})
        otp = change_password_data.get('otp', '')
        new_password = change_password_data.get('new_password', '')


        if not otp:
            raise serializers.ValidationError('OTP Expired')
        elif attempts >= 3:
            cache.delete(f"change_password:{user.id}")
            cache.delete(attempts_key)
            raise serializers.ValidationError('Too many attempts. Request new OTP')
        elif otp != otp_code:
            cache.set(attempts_key, attempts + 1, timeout=300)
            raise serializers.ValidationError('Incorrect OTP')

        user.password = new_password
        user.save()
        cache.delete(f"change_password:{user.id}")

        return {"message": 'Password Changed Successfully'}
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate(self, attrs):
        email = attrs.pop('email')
        
        try:
          user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid Email Address')
        
        token = secrets.token_urlsafe(32)

        cache.set(f"reset_token:{token}", user.id, timeout=600)

        frontend_url = settings.FRONTEND_BASE_URL

        reset_link = f"{frontend_url}/reset-password/?token={token}"

        send_reset_link_email(user.email, reset_link)
        return {
            "message": "Success"
        }
        
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        user_token = attrs.pop('token')
        new_password = attrs.pop('new_password')

        user_id = cache.get(f"reset_token:{user_token}", 0)

        if not user_id:
            raise serializers.ValidationError('Reset link expired')
        
        user = User.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()

        cache.delete(f"reset_token:{user_token}")

        return {'message': 'Password reset successfully'}

class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
