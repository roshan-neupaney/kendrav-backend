from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name']
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")
        return email
    
    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')

        try:
            user = User.objects.create_user(
                username = validated_data['email'],
                email = validated_data['email'],
                password = validated_data['password']
            )
        except Exception:
            raise serializers.ValidationError("Error creating user")
        if hasattr(user, 'profile'):
            user.profile.full_name = full_name
            user.profile.save()
        
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid Email')
        
        if not user.check_password(password):
            raise serializers.ValidationError('Incorrect Password')
        
        data = super().validate(attrs)
        access_token = data.pop('access')
        refresh_token = data.pop('refresh')

        data['access_token'] = access_token
        data['refresh_token'] = refresh_token

        return data