from rest_framework.views import APIView
from .serializers import SignedUploadCredentialsSerializer
import cloudinary
from django.conf import settings
import time
from rest_framework.response import Response
from rest_framework import status


class SignedUploadCredentialsView(APIView):
    def post(self, request):

        serializer = SignedUploadCredentialsSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            file_name = serializer.validated_data.pop("file_name")
            context = serializer.validated_data.pop("context")
            api_secret = settings.CLOUDINARY_API_SECRET
            api_key = settings.CLOUDINARY_API_KEY
            cloud_name = settings.CLOUDINARY_CLOUD_NAME
            timestamp = int(time.time())

            params_to_sign = {
                "timestamp": timestamp,
                "public_id": f"{file_name}_{timestamp}",
                "folder": context,
            }

            signature = cloudinary.utils.api_sign_request(
                params_to_sign=params_to_sign, api_secret=api_secret
            )

            return Response(
                {
                    "message": "Success",
                    "data": {
                        "signature": signature,
                        "api_key": api_key,
                        "cloud_name": cloud_name,
                        "timestamp": timestamp,
                        "folder": context,
                        "public_id": f"{file_name}_{timestamp}",
                    },
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
