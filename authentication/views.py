from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    ActiveSessionSerializer,
    ChangePasswordSerializer,
    ChangePasswordOTPSerializer
)
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework.permissions import AllowAny
from django.db import transaction
from users.models import UserToken
from rest_framework_simplejwt.tokens import RefreshToken


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


class GoogleLoginView(SocialLoginView):
    permission_classes = [AllowAny]
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:5173/login/google/callback"
    authentication_classes = []  # ADD — view must be publicly accessible


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
        serializer = ChangePasswordOTPSerializer(data=request.data, context={"user": user})
        if serializer.is_valid(raise_exception=True):
            return Response(
                {
                    "message": "Password Changed Successfully",
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)