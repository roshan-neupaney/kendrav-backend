from rest_framework import serializers
from .models import Post, PostMedia
from channels.models import ChannelPost
from channels.serializers import WorkspaceChannelSerializer
from workspaces.models import Workspace


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

    def create(self, validated_data):
        post_media = validated_data.pop("post_media", [])
        workspace_id = self.context.get("workspace_id")
        user = self.context.get("request").user

        workspace = Workspace.objects.filter(id=workspace_id, is_active=True).first()

        if workspace is None:
            raise serializers.ValidationError("Workspace not found")

        post = Post.objects.create(
            **validated_data, workspace=workspace, created_by=user
        )

        instance = [PostMedia(**media, post=post) for media in post_media]

        PostMedia.objects.bulk_create(instance)

        return post
