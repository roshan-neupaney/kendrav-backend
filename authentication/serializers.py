from rest_framework import serializers
from django.contrib.auth.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        full_name = validated_data.pop('full_name')

        user = User.objects.create_user(
            username = validated_data['email'],  # Using email as username
            email = validated_data['email'],
            password = validated_data['password']
        )

        if hasattr(user, 'profile'):
            user.profile.full_name = full_name
            user.profile.save()
        
        return user