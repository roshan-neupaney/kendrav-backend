from rest_framework import serializers
from .models import Channel, WorkspaceChannel, ChannelConfig
from channels.oauth_handlers import oauth_handler
from django.conf import settings
import requests
from workspaces.models import Workspace
from django.core.cache import cache


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
        config = data.pop("config")
        config.pop("access_token")
        data["config"] = config
        return data


class ExchangeCodeSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True)
    channel_id = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all(), write_only=True
    )


class WorkspaceChannelSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    channel_config = ChannelConfigSerializer(read_only=True)

    channel_id = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all(), write_only=True
    )
    uuid = serializers.CharField(write_only=True)
    page_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True, write_only=True
    )

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

        workspace_id = self.context.get("workspace_id", "")
        page_ids = validated_data.pop("page_ids")
        uuid = validated_data.pop("uuid")

        workspace = Workspace.objects.filter(id=workspace_id, is_active=True).first()

        if workspace is None:
            raise serializers.ValidationError("Workspace not found")

        cache_data = cache.get(f"user_page_list:{uuid}")

        if not cache_data:
            serializers.ValidationError("Session Expired")

        cache_pages = cache_data.get("pages", None)
        cache_channel = cache_data.get("channel")

        handler = oauth_handler(cache_channel)

        pages = [page for page in cache_pages if page.id in page_ids]

        result = handler.get_page_data(pages)

        full_name = result.get("full_name", "")
        access_token = result.get("access_token", "")
        expires_at = result.get("expires_at", "")
        account_id = result.get("account_id", "")
        profile_picture = result.get("profile_picture", "")

        config = {
            "access_token": access_token,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

        workspace_channel = (
            WorkspaceChannel.objects.prefetch_related("channel_config")
            .filter(channel=channel, workspace=workspace, account_id=account_id)
            .first()
        )

        if workspace_channel is None:
            workspace_channel = WorkspaceChannel.objects.create(
                channel=channel,
                workspace=workspace,
                account_id=account_id,
                full_name=full_name,
                profile_picture=profile_picture,
            )
            ChannelConfig.objects.create(
                workspace_channel=workspace_channel, config=config
            )
        elif workspace_channel.is_active:
            if not hasattr(workspace_channel, "channel_config"):
                ChannelConfig.objects.create(
                    workspace_channel=workspace_channel, config=config
                )
            raise serializers.ValidationError("Workspace channel already exists")
        else:
            workspace_channel.is_active = True
            if hasattr(workspace_channel, "channel_config"):
                workspace_channel.channel_config.config = config
                workspace_channel.channel_config.save()
            else:
                ChannelConfig.objects.create(
                    workspace_channel=workspace_channel, config=config
                )

            workspace_channel.save()

        return workspace_channel
