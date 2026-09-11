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

    def post(self, request):
        serializer = ChannelSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "status": status.HTTP_201_CREATED,
                    "message": "Channels created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
