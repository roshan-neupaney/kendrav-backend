from rest_framework import serializers
from .models import UserNotification, Notification
from users.models import UserFcmToken
from workspaces.models import Workspace
from django.contrib.auth import get_user_model
from .tasks import subscribe_to_all_topic
from firebase_admin import messaging

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "title",
            "body",
            "image_url",
            "action_type",
            "redirect_url",
            "is_active",
        ]


# In notifications/serializers.py — don't import from workspaces
class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "title", "slug_url"]


class UserNotificationSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = UserNotification
        fields = "__all__"


class RegisterFCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFcmToken
        fields = "__all__"
        extra_kwargs = {"user": {"required": False}}

    def create(self, validated_data):
        user = self.context["user"]

        fcm_token = validated_data.pop("fcm_token")
        device_id = validated_data.get("device_id")

        user_workspace_slugs = list(
            Workspace.objects.filter(
                is_active=True, workspace_members__user=user
            ).values_list("slug_url", flat=True)
        )

        UserFcmToken.objects.filter(
            user=user, device_id=device_id, is_active=True
        ).exclude(fcm_token=fcm_token).update(is_active=False)

        for workspace_slug in user_workspace_slugs:
            subscribe_to_all_topic.delay(
                workspace_slug=workspace_slug, user=user.id, fcm_token=fcm_token
            )

        user_fcm_token, is_created = UserFcmToken.objects.get_or_create(
            user=user, fcm_token=fcm_token, device_id=device_id
        )

        if not is_created and not user_fcm_token.is_active:
            user_fcm_token.is_active = True
            user_fcm_token.save()

        return user_fcm_token
