from rest_framework import serializers
from .models import Post, PostMedia
from channels.models import ChannelPost, WorkspaceChannel
from channels.serializers import WorkspaceChannelSerializer
from workspaces.models import Workspace
from datetime import datetime, timezone
from .tasks import publish_post_to_channel


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = "__all__"


class ChannelPostSerializer(serializers.ModelSerializer):
    workspace_channel = WorkspaceChannelSerializer(read_only=True)

    class Meta:
        model = ChannelPost


class PostSerializer(serializers.ModelSerializer):
    post_medias = serializers.SerializerMethodField()
    channel_posts = ChannelPostSerializer(read_only=True, many=True)

    post_media = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    delete_medias = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    def get_post_medias(self, instance):
        active_medias = instance.post_medias.filter(is_active=True)
        return PostMediaSerializer(active_medias, many=True).data

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

    def update(self, instance, validated_data):
        post_media = validated_data.pop("post_media", None)
        delete_medias = validated_data.pop("delete_medias", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if post_media and len(post_media) > 0:
            fields_to_update = set()

            objects_to_create = []
            objects_to_update = []

            for item in post_media:
                post_media_id = item.pop("id", None)

                if post_media_id:
                    update_media_instance = PostMedia(id=post_media_id, post=instance)

                    for key, value in item.items():
                        if key != "id":
                            setattr(update_media_instance, key, value)
                            fields_to_update.add(key)

                    objects_to_update.append(update_media_instance)

                else:
                    create_media_instance = PostMedia(**item, post=instance)
                    objects_to_create.append(create_media_instance)

            if delete_medias and len(delete_medias) > 0:
                delete_instances = PostMedia.objects.filter(id__in=delete_medias)
                for delete_instance in delete_instances:
                    delete_instance.is_active = False
                    fields_to_update.add("is_active")
                    objects_to_update.append(delete_instance)

            if objects_to_create:
                PostMedia.objects.bulk_create(objects_to_create)

            if objects_to_update and fields_to_update:
                PostMedia.objects.bulk_update(
                    objects_to_update, fields=fields_to_update
                )

        instance.save()

        return instance


class PostPublishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"

    def update(self, instance, validated_data):
        status = validated_data.get("status", "")

        if status == "draft":
            instance.status = "draft"
            return instance.save()
        else:
            instance.status = "pending"
            workspace_channel_ids = instance.workspace_channel_ids
            if workspace_channel_ids and len(workspace_channel_ids) > 0:
                workspace_channel_existing_ids = ChannelPost.objects.filter(
                    workspace_channel__in=workspace_channel_ids, post=instance
                ).values_list("workspace_channel")
                channel_post_instances = []
                for id in workspace_channel_ids:
                    if id not in workspace_channel_existing_ids:
                        channel_post_instance = ChannelPost(
                            workspace_channel=id, post=instance
                        )
                        channel_post_instances.append(channel_post_instance)

                ChannelPost.objects.bulk_create(channel_post_instances)
            else:
                serializers.ValidationError("At least one channel is required")
            
            if status == 'now':
                publish_post_to_channel.delay()

        instance.save()

        return instance
