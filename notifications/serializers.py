from rest_framework import serializers
from .models import UserNotification, Notification
from users.models import UserFcmToken
from workspaces.models import Workspace
from django.contrib.auth import get_user_model

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
        fields = ['id', 'title', 'slug_url']


class UserNotificationSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = UserNotification
        fields = "__all__"
    

class RegisterFCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserFcmToken
        fields='__all__'
        extra_kwargs = {
            "user": {'required': False}
        }
    
    def create(self, validated_data):
        user = self.context['user']

        fcm_token = validated_data.pop('fcm_token')
        device_id = validated_data.get('device_id')

        UserFcmToken.objects.filter(user=user, device_id=device_id, is_active=True).delete()


        user_fcm_token = UserFcmToken.objects.create(user=user, fcm_token=fcm_token, device_id=device_id)

        return user_fcm_token