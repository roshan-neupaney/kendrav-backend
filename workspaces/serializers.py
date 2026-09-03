from .models import Workspace
from rest_framework import serializers
from .utils import generate_workspace_slug

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'title', 'slug_url']
    
    def create(self, validated_data):
        title = validated_data['title']
        slug_url = validated_data['slug_url']
        workspace = Workspace.objects.get_or_create(title=title, slug_url = slug_url)

        workspace.slug_url = generate_workspace_slug(title, workspace_id=workspace.id)
        workspace.save()
        return workspace
        
    
class WorkspaceWithIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'title', 'slug_url', 'type']
    