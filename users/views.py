from .serializers import UserSerializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class UserView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserSerializers(user)
        return Response(
            {
                "message": "Users fetched successfully.",
                "data": serializer.data,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )
