from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile, Preference, UserSubscription
from notifications.models import UserNotification

User = get_user_model()


class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = "__all__"
        exclude = ["user"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"
        exclude = ["user"]


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class UserSubsctiptions(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'
        exclude = ['user']