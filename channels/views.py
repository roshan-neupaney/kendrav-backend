from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.permission import IsSuperAdmin


class ChannelView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response(
            {"status": status.HTTP_200_OK, "message": "Channels retrived successfully"}
        )
