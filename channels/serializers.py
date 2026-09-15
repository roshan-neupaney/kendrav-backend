from rest_framework import serializers
from .models import Channel, WorkspaceChannel
from channels.utils import exchange_code_for_token, exchange_long_lived_token
from django.conf import settings


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = [
            "id",
            "image_url",
            "channel_url",
            "title",
            "slug_url"
            "is_active",
            "created_at",
            "updated_at",
        ]


class WorkspaceChannelSerializer(serializers.ModelSerializer):
    # channel = ChannelSerializer()

    channel_id = serializers.CharField()
    code = serializers.CharField(write_only=True)

    class Meta:
        model = WorkspaceChannel
        fields = [
            "id",
            # "workspace",
            # "channel",
            "code",
            "channel_id",
            # "email",
            # "username",
            "account_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
    
    def create(self, validated_data):
        channel_id = validated_data.get('channel_id', '')
        code = validated_data.get('code', '')

        channel = Channel.objects.filter(id=channel_id).first()
        if channel is None:
            serializers.ValidationError('Channel not found')
        
        redirect_url = f"{settings.FRONTEND_BASE_URL}/channel/facebook/callback"

        exchange_code = exchange_code_for_token(code=code, redirect_uri=redirect_url)

        result = exchange_long_lived_token(token=exchange_code.get('access_token'), redirect_uri=redirect_url)
        print(result)

        return result

