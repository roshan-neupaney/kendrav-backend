from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    ActiveSessionSerializer,
    ChangePasswordSerializer,
    ChangePasswordOTPSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    GoogleLoginSerializer,
    RefreshTokenSerializer,
)
from rest_framework.permissions import AllowAny
from django.db import transaction
from users.models import UserToken
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.exceptions import TokenError
from django.core.cache import cache
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.authentication import AuthenticationFailed

User = get_user_model()


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                result = serializer.save()

                return Response(
                    {
                        "message": "Account Created Successfully",
                        "status": status.HTTP_201_CREATED,
                        "data": {
                            "refresh_token": result["refresh_token"],
                            "access_token": result["access_token"],
                        },
                    },
                    status=status.HTTP_201_CREATED,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                result = serializer.save()

                return Response(
                    {
                        "message": "Login Successfully",
                        "status": status.HTTP_200_OK,
                        "data": {
                            "refresh_token": result["refresh_token"],
                            "access_token": result["access_token"],
                        },
                    },
                    status=status.HTTP_200_OK,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            id_token = serializer.validated_data.get("id_token")
            device_id = serializer.validated_data.get("device_id")
            device_name = serializer.validated_data.get("device_name", "")
            location = serializer.validated_data.get("location", "")

            try:
                tokenExist = cache.get(f"used_google_token:{id_token}", 0)
                if tokenExist:
                    return Response(
                        {
                            "message": ["Token already used"],
                            "status": status.HTTP_400_BAD_REQUEST,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                id_info = google_id_token.verify_oauth2_token(
                    id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
                )

                if id_info["iss"] not in [
                    "accounts.google.com",
                    "https://accounts.google.com",
                ]:
                    raise ValueError("Wrong issuer.")

                cache.set(f"used_google_token:{id_token}", 1, timeout=3600)

                name_parts = id_info.get("name", "").split(" ")
                profile_picture = id_info.get("picture", "")
                is_email_verified = id_info.get("email_verified", False)
                email = id_info.get("email", "")
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                with transaction.atomic():
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": email,
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )

                    if created and name_parts and hasattr(user, "profile"):
                        user.profile.full_name = " ".join(name_parts)
                        user.profile.profile_picture = profile_picture
                        user.profile.is_email_verified = is_email_verified
                        user.profile.save()

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
                        device_id=device_id,
                        device_name=device_name,
                        location=location,
                    )
                    return Response(
                        {
                            "message": "Login Successfully",
                            "data": {
                                "access_token": access_token,
                                "refresh_token": refresh_token,
                            },
                            "status": status.HTTP_200_OK,
                        },
                        status=status.HTTP_200_OK,
                    )

            except ValueError as e:
                return Response(
                    {
                        "message": ["Invalid Google Token"],
                        "status": status.HTTP_400_BAD_REQUEST,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutView(APIView):
    def post(self, request):
        user = request.user
        device_id = request.headers.get("deviceId", "")

        if not device_id:
            return Response(
                {
                    "message": ["Device id is required"],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user_tokens = UserToken.objects.filter(
                user=user, device_id=device_id, is_active=True
            )
            for token_data in user_tokens:
                old_refresh_token = RefreshToken(token_data.refresh_token)
                old_refresh_token.blacklist()
                token_data.is_active = False

            UserToken.objects.bulk_update(user_tokens, ["is_active"])

            return Response(
                {"message": "Logout Successfully", "status": status.HTTP_200_OK},
                status=status.HTTP_200_OK,
            )


class LogoutAllView(APIView):
    def post(self, request):
        user = request.user

        with transaction.atomic():
            user_tokens = UserToken.objects.filter(user=user, is_active=True)

            for token_data in user_tokens:
                old_refresh_token = RefreshToken(token_data.refresh_token)
                old_refresh_token.blacklist()
                token_data.is_active = False

            UserToken.objects.bulk_update(user_tokens, ["is_active"])
            return Response(
                {
                    "message": "Logout From all devices Successfully",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )


class LogoutDeviceView(APIView):
    def post(self, request):
        user = request.user
        user_device_id = request.headers.get("deviceId", "")
        device_id = request.data.get("device_id", "")

        if not user_device_id:
            return Response(
                {
                    "message": ["User device id is required"],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not device_id:
            return Response(
                {
                    "message": ["Device id is required"],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user_tokens = UserToken.objects.filter(
                user=user, device_id=device_id, is_active=True
            )

            for token_data in user_tokens:
                old_refresh_token = RefreshToken(token_data.refresh_token)
                old_refresh_token.blacklist()
                token_data.is_active = False

            UserToken.objects.bulk_update(user_tokens, ["is_active"])
            return Response(
                {
                    "message": "Logout From Device Successfully",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )


class ActiveSessionView(APIView):
    def get(self, request):
        user = request.user
        user_tokens = UserToken.objects.filter(user=user, is_active=True)
        serializer = ActiveSessionSerializer(user_tokens, many=True)
        return Response(
            {
                "message": "Active Sessions Fetched Successfully",
                "data": serializer.data,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data, context={"user": user})
        if serializer.is_valid(raise_exception=True):
            return Response(
                {
                    "message": "OTP code is sent to your email",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordOTPView(APIView):
    def post(self, request):
        user = request.user
        serializer = ChangePasswordOTPSerializer(
            data=request.data, context={"user": user}
        )
        if serializer.is_valid(raise_exception=True):
            return Response(
                {
                    "message": "Password Changed Successfully",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print('enter post method')
        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            print('serializer is valid')
            return Response(
                {
                    "message": "Reset Link is sent to your email.",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(
                {
                    "message": "Password reset successfully.",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            device_id = request.headers.get("deviceId", "")
            refresh = serializer.validated_data.get("refresh", "")

            if not device_id:
                raise AuthenticationFailed("Device Id is required")

            with transaction.atomic():
                response = super().post(request, *args, **kwargs)
                if response.status_code == 200:
                    refresh_token = response.data["refresh"]

                    UserToken.objects.filter(
                        device_id=device_id, refresh_token=refresh
                    ).update(refresh_token=refresh_token)

                    return Response(
                        {
                            "message": "Token refreshed Successfully",
                            "data": {
                                "access_token": response.data["access"],
                                "refresh_token": response.data["refresh"],
                            },
                            "status": status.HTTP_200_OK,
                        },
                        status=status.HTTP_200_OK,
                    )

        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_401_UNAUTHORIZED,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
