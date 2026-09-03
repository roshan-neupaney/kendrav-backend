from .models import Workspace
from rest_framework import serializers

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'title', 'slug_url']