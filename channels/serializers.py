from rest_framework import serializers
from .models import Channel, WorkspaceChannel


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = [
            "id",
            "image_url",
            "channel_url",
            "title",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class WorkspaceChannelSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer()

    class Meta:
        model = WorkspaceChannel()
        fields = [
            "id",
            "workspace",
            "channel",
            "email",
            "username",
            "account_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
