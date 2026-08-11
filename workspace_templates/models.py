from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Template(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='workspace_templates')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_templates')
    is_global = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)