from django.db import models

StatusChoices = [
    ('pending', 'Pending'),
    ('failed', 'Failed'),
    ('published', 'Published'),
    ('process_failed', 'Process Failed'),
]

class Channel(models.Model):
    title = models.CharField(max_length=100)
    image_url = models.CharField(max_length=300, blank=True, null=True)
    channel_url = models.CharField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorkspaceChannel(models.Model):
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='workspace_channels')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='channel_workspaces')
    email = models.EmailField()
    username = models.CharField(max_length=100)
    account_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ChannelConfig(models.Model):
    workspace_channel = models.OneToOneField(WorkspaceChannel, on_delete=models.CASCADE, related_name='channel_config')
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ChannelPost(models.Model):
    workspace_channel = models.ForeignKey(WorkspaceChannel, on_delete=models.CASCADE, related_name='channel_posts')
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, related_name='post_channels')
    status = models.CharField(max_length=50, default='pending', choices=StatusChoices)
    published_at = models.DateTimeField(blank=True, null=True)
    platform_post_id = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)