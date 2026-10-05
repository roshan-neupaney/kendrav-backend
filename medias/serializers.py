from rest_framework import serializers

class SignedUploadCredentialsSerializer(serializers.Serializer):
    file_name = serializers.CharField(write_only=True, required=True)
    context = serializers.CharField(write_only=True, required=True)