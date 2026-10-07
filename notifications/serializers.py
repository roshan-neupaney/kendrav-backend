from rest_framework import serializers
from .models import UserNotification, Notification, NotificationPreference
from users.models import UserFcmToken
from workspaces.models import Workspace, WorkspaceMember
from django.contrib.auth import get_user_model
from firebase_admin import messaging
from .tasks import subscribe_to_topic, unsubscribe_from_topic

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

        existing_tokens = UserFcmToken.objects.filter(user=user, device_id=device_id)

        existing_token_list = list(
            existing_tokens.all().values_list("fcm_token", flat=True)
        )

        if len(existing_token_list) > 0:
            existing_tokens.delete()

            for workspace_slug in user_workspace_slugs:
                unsubscribe_from_topic.delay(
                    workspace_slug=workspace_slug,
                    user=user.id,
                    fcm_tokens=existing_token_list,
                )

        for workspace_slug in user_workspace_slugs:
            subscribe_to_topic.delay(
                workspace_slug=workspace_slug, user=user.id, fcm_token=fcm_token
            )


        user_fcm_token = UserFcmToken.objects.create(
            user=user, fcm_token=fcm_token, device_id=device_id
        )

        return user_fcm_token
