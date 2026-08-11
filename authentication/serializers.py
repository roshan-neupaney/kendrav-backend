from rest_framework import serializers, status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserToken

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


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid Email")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect Password")

        attrs[self.username_field] = user.username
        data = super().validate(attrs)

        data["access_token"] = data.pop("access")
        data["refresh_token"] = data.pop("refresh")

        return {
            "message": "Login Successfull",
            "data": data,
            "status": status.HTTP_200_OK,
        }
