from rest_framework import serializers
from .models import Post, PostMedia
from channels.models import ChannelPost, WorkspaceChannel
from channels.serializers import WorkspaceChannelSerializer
from workspaces.models import Workspace, MyTime
from datetime import datetime, timezone, timedelta
from .tasks import publish_post_to_channel
from zoneinfo import ZoneInfo
from .utils import convert_to_user_timezone


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

    schedule_date = serializers.DateField(required=False, write_only=True)
    schedule_time = serializers.TimeField(required=False, write_only=True)

    def get_post_medias(self, instance):
        active_medias = instance.post_medias.filter(is_active=True)
        return PostMediaSerializer(active_medias, many=True).data

    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["created_by", "workspace"]

    def validate(self, attrs):
        schedule_time = attrs.pop("schedule_time", "")
        schedule_date = attrs.pop("schedule_date", "")

        if schedule_date and schedule_time:
            user_timezone = self.context.get("request").user.preference.timezone
            current_date = datetime.now(timezone.utc)
            schedule_date_time = datetime.combine(schedule_date, schedule_time)

            schedule_dt_utc = convert_to_user_timezone(
                user_timezone=user_timezone, date_time=schedule_date_time
            )

            if current_date > schedule_dt_utc:
                raise serializers.ValidationError(
                    "Schedule date time cannot be in past"
                )

            attrs["schedule_date_time"] = schedule_dt_utc

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
    post_status = serializers.CharField(
        required=False,
        write_only=True,
    )

    class Meta:
        model = Post
        fields = "__all__"

    def update(self, instance, validated_data):
        post_status = validated_data.get("post_status", "")
        workspace_id = self.context.get("workspace_id")
        user = self.context.get("request").user

        valid_status = ['draft', 'schedule', 'my_time', 'now']

        if post_status not in valid_status:
            raise serializers.ValidationError(f'{post_status} is not valid status')

        if post_status == "draft":
            instance.status = "draft"
            instance.save()
            return instance

        workspace_channel_ids = instance.workspace_channel_ids

        if not workspace_channel_ids:
            raise serializers.ValidationError("At least one channel is required")

        if post_status == "now":
            instance.status = "pending"
            instance.save()
            publish_post_to_channel.delay(post_id=instance.id)

        if post_status == "my_time":
            days = {
                "Monday": 1,
                "Tuesday": 2,
                "Wednesday": 3,
                "Thursday": 4,
                "Friday": 5,
                "Saturday": 6,
                "Sunday": 7,
            }
            my_times = MyTime.objects.filter(is_active=True, workspace=workspace_id)
            my_time_list = list(my_times.all())

            available_slot_dates = []

            now = datetime.now(timezone.utc)
            today = now.isoweekday()

            week_no = 1

            while not len(available_slot_dates) > 0:
                for time_slot in my_time_list:
                    slot_day = time_slot.day
                    slot_time = time_slot.time
                    slot_day_number = days.get(slot_day)
                    day_diff = (
                        7 * (week_no - 1) + slot_day_number - today
                        if slot_day_number >= today
                        else (7 * week_no - today) + slot_day_number
                    )
                    slot_date = now + timedelta(days=day_diff)
                    slot_date_time = datetime.combine(slot_date.date(), slot_time)
                    slot_date_time_utc = convert_to_user_timezone(
                        user_timezone=user.preference.timezone,
                        date_time=slot_date_time,
                    )

                    post = Post.objects.filter(
                        schedule_date_time=slot_date_time_utc,
                        workspace=workspace_id,
                        status="pending",
                    ).first()

                    if post is None and slot_date_time_utc > now:
                        available_slot_dates.append(slot_date_time_utc)

                week_no += 1

            next_slot = min(available_slot_dates)
            instance.status = "pending"
            instance.schedule_date_time = next_slot

        elif post_status == "schedule":
            schedule_date_time = instance.schedule_date_time
            if not schedule_date_time:
                raise serializers.ValidationError(
                    "Schedule date and time are required"
                )
            instance.status = "pending"

        existing_post_channel = ChannelPost.objects.filter(post=instance)
        
        channel_post_instances = []

        existing_post_channel_list = list(
            existing_post_channel.values_list("workspace_channel_id", flat=True)
        )

        new_channels = [
            id
            for id in workspace_channel_ids
            if id not in existing_post_channel_list
        ]

        removed_channels = [
            id
            for id in existing_post_channel_list
            if id not in workspace_channel_ids
        ]

        for id in new_channels:
            workspace_channel = WorkspaceChannel.objects.filter(
                id=id, is_active=True
            ).first()

            if workspace_channel:
                channel_post_instance = ChannelPost(
                    workspace_channel=workspace_channel, post=instance
                )
                channel_post_instances.append(channel_post_instance)

        ChannelPost.objects.bulk_create(channel_post_instances)

        for id in removed_channels:
            removed_channel_post = existing_post_channel.filter(
                workspace_channel=id
            ).first()

            removed_channel_post.delete()

        instance.save()

        return instance
