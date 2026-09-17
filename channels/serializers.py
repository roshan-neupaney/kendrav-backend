from rest_framework import serializers
from .models import Channel, WorkspaceChannel, ChannelConfig
from channels.oauth_handlers import oauth_handler
from django.conf import settings
import requests
from workspaces.models import Workspace


class ChannelSerializer(serializers.ModelSerializer):
    slug_url = serializers.SlugField(required=False)

    class Meta:
        model = Channel
        fields = [
            "id",
            "image_url",
            "channel_url",
            "title",
            "slug_url",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ChannelConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelConfig
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        config = data.pop('config')
        config.pop('access_token')
        data['config'] = config
        return data

class WorkspaceChannelSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    channel_config = ChannelConfigSerializer(read_only=True)

    channel_id = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.all(), write_only=True)
    code = serializers.CharField(write_only=True)

    class Meta:
        model = WorkspaceChannel
        fields = [
            "id",
            "workspace_id",
            "channel",
            "code",
            "channel_id",
            "username",
            "account_id",
            "channel_config",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        channel = validated_data.get("channel_id")
        code = validated_data.get("code", "")
        workspace_id = self.context.get("workspace_id", "")

        workspace = Workspace.objects.filter(id=workspace_id, is_active=True).first()


        if workspace is None:
            raise serializers.ValidationError("Workspace not found")

        handler = oauth_handler(slug_url=channel.slug_url)

        result = handler.exchange_token(code=code)

        if not result.get("status"):
            raise serializers.ValidationError(result.get('message'))

        full_name = result.get("full_name", "")
        access_token = result.get("access_token", "")
        expires_at = result.get("expires_at", "")
        account_id = result.get("account_id", "")
        profile_picture = result.get("profile_picture", "")

        workspace_channel_exist = WorkspaceChannel.objects.filter(channel=channel, workspace=workspace, account_id=account_id).exists()

        if workspace_channel_exist:
            raise serializers.ValidationError('User channel already exists')

        workspace_channel = WorkspaceChannel.objects.create(
            channel=channel,
            workspace=workspace,
            account_id=account_id,
            full_name=full_name,
            profile_picture=profile_picture,
        )

        config = {
            "access_token": access_token,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        ChannelConfig.objects.create(workspace_channel=workspace_channel, config=config)
        
        return workspace_channel
