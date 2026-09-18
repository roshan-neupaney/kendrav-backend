from rest_framework import serializers
from .models import Post, PostMedia
from channels.models import ChannelPost
from channels.serializers import WorkspaceChannelSerializer
from workspaces.models import Workspace
from datetime import datetime, timezone


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = "__all__"


class ChannelPostSerializer(serializers.ModelSerializer):
    workspace_channel = WorkspaceChannelSerializer(read_only=True)

    class Meta:
        model = ChannelPost


class PostSerializer(serializers.ModelSerializer):
    post_medias = PostMediaSerializer(read_only=True, many=True)
    channel_posts = ChannelPostSerializer(read_only=True, many=True)

    post_media = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["created_by", "workspace"]

    def validate(self, attrs):
        schedule_time = attrs.get("schedule_time", "")
        schedule_date = attrs.get("schedule_date", "")

        if bool(schedule_date) ^ bool(schedule_time):
            raise serializers.ValidationError("Both schedule date and time is requried")

        elif schedule_date and schedule_time:
            current_date = datetime.now(timezone.utc)
            schedule_date_time = datetime.combine(
                schedule_date, schedule_time, tzinfo=timezone.utc
            )
            if current_date > schedule_date_time:
                raise serializers.ValidationError(
                    "Schedule date time cannot be in past"
                )

        return attrs

    def create(self, validated_data):
        post_media = validated_data.pop("post_media", [])
        workspace_id = self.context.get("workspace_id")

        workspace = Workspace.objects.filter(id=workspace_id, is_active=True).first()

        if workspace is None:
            raise serializers.ValidationError("Workspace not found")

        post = Post.objects.create(**validated_data, workspace=workspace)

        instance = [PostMedia(**media, post=post) for media in post_media]

        PostMedia.objects.bulk_create(instance)

        return post
