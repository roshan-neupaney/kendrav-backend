from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile, Preference, UserSubscription
from workspaces.models import Workspace
from notifications.models import NotificationPreference

User = get_user_model()


class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        exclude = ["user"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ["user"]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        exclude = ["user"]

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        exclude = ["owner"]


class NotificationPreferenceSerializers(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        exclude = ["user"]


class UserSerializers(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    preference = PreferencesSerializer(read_only=True)
    workspaces = WorkspaceSerializer(many=True, read_only=True)
    notification_preferences = NotificationPreferenceSerializers(
        many=True, read_only=True
    )

    user_subscription = serializers.SerializerMethodField()
    def get_user_subscription(self, instance):
        subscription = UserSubscription.objects.filter(user=instance,is_active=True).first()
        if subscription:
            return UserSubscriptionSerializer(subscription).data
        return None

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "profile",
            "preference",
            "workspaces",
            "user_subscription",
            "notification_preferences",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        notification_preferences = data.pop("notification_preferences", [])
        result = {}
        for item in notification_preferences:
            result[item["notification_type"]] = item["is_permitted"]

        data["notification_preferences"] = result
        return data
