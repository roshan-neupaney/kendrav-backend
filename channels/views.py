from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.permission import IsSuperAdmin
from .models import Channel
from .serializers import ChannelSerializer


class ChannelView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        channel = Channel.objects.filter(is_active=True)

        serializer = ChannelSerializer(channel, many=True)
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Channels retrived successfully",
                "data": serializer.data,
            }
        )
