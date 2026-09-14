from rest_framework import serializers
from .models import Channel


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ["id", "image_url", "channel_url", "title", "is_active", "is_deleted", "created_at", "updated_at"]
