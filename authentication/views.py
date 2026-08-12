from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework.permissions import AllowAny
from django.db import transaction


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
                            "refresh_token": result['refresh_token'],
                            "access_token": result['access_token'],
                        }
                    }, status=status.HTTP_201_CREATED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data, headers=request.headers)
        if serializer.is_valid(raise_exception=True):
            serializer.save()


class GoogleLoginView(SocialLoginView):
    permission_classes = [AllowAny]
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = 'http://localhost:5173/login/google/callback'
    authentication_classes = []   # ADD — view must be publicly accessible
