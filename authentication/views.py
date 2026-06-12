from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegistrationSerializer, LoginSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class RegistrationView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Account Created Successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.data["email"]
            password = serializer.data["password"]

            user = User.objects.filter(email=email)
            if not user.exists():
                return Response(
                    {
                        "message": "User does not exist",
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )

            user = authenticate(username=user.first().username, password=password)

            if user is None:
                return Response(
                    {
                        "message": "Invalid Password",
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login Successful",
                    "data": {
                        "refresh_token": str(refresh),
                        "access_token": str(refresh.access_token),
                    },
                    "status": status.HTTP_200_OK,
                },
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
