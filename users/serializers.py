from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile, Preference

User = get_user_model()


class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = "__all__"
        exclude = ["id", "user"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"
        exclude = ["id", "user"]


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
