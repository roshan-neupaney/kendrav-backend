from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.permission import IsSuperAdmin
from .models import Channel, WorkspaceChannel
from .serializers import (
    ChannelSerializer,
    WorkspaceChannelSerializer,
    ExchangeCodeSerializer,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from workspaces.permission import IsWorkspaceMember, HasWorkspacePermission
from .oauth_handlers import oauth_handler
from datetime import datetime, timezone


class ChannelView(APIView):
    # def get_permissions(self):
    #     method_permissions = {"GET": [AllowAny()], "POST": [IsSuperAdmin()]}
    #     return method_permissions.get(self.request.method, [IsAuthenticated()])

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
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChannelWithIdView(APIView):
    permission_classes = [IsSuperAdmin]

    def patch(self, request, channel_id):
        channel = Channel.objects.filter(is_active=True, id=channel_id).first()

        serializer = ChannelSerializer(channel, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                {
                    "message": "Channel updated successfully",
                    "status": status.HTTP_200_OK,
                    "data": serializer.data,
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

    def delete(self, request, channel_id):
        channel = Channel.objects.filter(is_active=True, id=channel_id).first()

        if channel is None:
            return Response(
                {
                    "message": "Channel not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        channel.is_active = False
        channel.save()

        return Response(
            {
                "message": "Channel deleted successfully",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class ExchangeCodeView(APIView):
    def post(self, request):
        serializer = ExchangeCodeSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            code = serializer.validated_data.get("code")
            channel = serializer.validated_data.get("channel_id")

            handler = oauth_handler(slug_url=channel.slug_url)
            result = handler.exchange_token(code=code)

            return Response(
                {
                    "message": "Page list retrived successfully",
                    "status": status.HTTP_200_OK,
                    "data": result,
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


class WorkspaceChannelView(APIView):
    def get_permissions(self):
        method_permissions = {
            "GET": [IsAuthenticated(), IsWorkspaceMember()],
            "POST": [
                IsAuthenticated(),
                HasWorkspacePermission("channels:can_connect")(),
            ],
        }
        return method_permissions.get(self.request.method, [IsAuthenticated()])

    def get(self, request, workspace_id):
        workspace_channel = WorkspaceChannel.objects.filter(
            is_active=True, workspace=workspace_id
        )

        serializer = WorkspaceChannelSerializer(workspace_channel, many=True)

        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Worksapce channels retrived successfully",
                "data": serializer.data,
            }
        )

    def post(self, request, workspace_id):
        serailzer = WorkspaceChannelSerializer(
            data=request.data, context={"workspace_id": workspace_id}
        )

        if serailzer.is_valid(raise_exception=True):
            serailzer.save()
            return Response(
                {
                    "message": "Workspace channel connected successfully",
                    "status": status.HTTP_200_OK,
                    "data": serailzer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": serailzer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class WorkspaceChannelWithIdView(APIView):
    def get_permissions(self):
        method_permissions = {
            "POST": [
                IsAuthenticated(),
                HasWorkspacePermission("channels:can_disconnect")(),
            ],
        }
        return method_permissions.get(self.request.method, [IsAuthenticated()])

    def post(self, request, workspace_id, workspace_channel_id):
        workspace_channel = (
            WorkspaceChannel.objects.prefetch_related("channel_config")
            .select_related("channel")
            .filter(id=workspace_channel_id, is_active=True)
            .first()
        )

        if workspace_channel is None:
            return Response(
                {
                    "message": "Workspace Channel not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = workspace_channel.channel_config.config
        access_token = config.get("access_token", "")

        if access_token:
            handler = oauth_handler(workspace_channel.channel.slug_url)
            handler.invalidate_token(workspace_channel.account_id, access_token)

        workspace_channel.is_active = False
        workspace_channel.channel_config.config = {}
        workspace_channel.channel_config.save()
        workspace_channel.save()
        return Response(
            {
                "message": "Workspace Channel Disconnected Successfully",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceChannelHealthView(APIView):
    permission_classes = [IsWorkspaceMember]

    def get(self, request, workspace_channel_id):
        workspace_channel = (
            WorkspaceChannel.objects.prefetch_related("channel_config")
            .select_related("channel")
            .filter(id=workspace_channel_id, is_active=True)
            .first()
        )

        if workspace_channel is None:
            return Response(
                {
                    "message": "Workspace Channel not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = workspace_channel.channel_config.config
        access_token = config.get("access_token", "")
        expires_at = config.get("expires_at", "")

        if not access_token:
            return Response(
                {
                    "message": "Token not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at_dt = datetime.fromisoformat(expires_at) if expires_at else None

        if expires_at_dt and expires_at_dt < datetime.now(timezone.utc):
            return Response(
                {
                    "message": "Token expired",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        handler = oauth_handler(workspace_channel.channel.slug_url)

        is_valid = handler.test_user_data(access_token)

        if not is_valid:
            return Response(
                {
                    "message": "Token invalid",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Workspace channel is healthy",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )
