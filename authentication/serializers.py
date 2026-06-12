from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import Profile

class RegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')

        user = User.objects.create_user(
            username = validated_data['email'].split('@')[0],
            email = validated_data['email'],
            password = validated_data['password']
        )

        if hasattr(user, 'profile'):
            user.profile.full_name = full_name
            user.profile.save()
        
        return user

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def get(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):
            return user
        raise serializers.ValidationError("Invalid email or password")