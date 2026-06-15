from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegistrationSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class RegistrationView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "message": "Account Created Successfully",
                    "status": status.HTTP_201_CREATED,
                },
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client