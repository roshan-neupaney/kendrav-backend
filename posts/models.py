from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

StatusChoices = [
    ('draft', 'Draft'),
    ('scheduled', 'Scheduled'),
    ('published', 'Published'),
    ('failed', 'Failed'),
    ('pending', 'Pending'),
    ('process_failed', 'Process Failed'),
    ('for_approval', 'For Approval'),
    ('rejected', 'Rejected')
]

MediaTypeChoices = [
    ('image', 'Image'),
    ('video', 'Video')
]

class Post(models.Model):
    caption = models.TextField(blank=True, null=True)
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='posts')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    location = models.CharField(max_length=255, blank=True, null=True)
    music = models.CharField(max_length=255, blank=True, null=True)
    feeling = models.CharField(max_length=255, blank=True, null=True)
    schedule_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default='draft', choices=StatusChoices)
    remarks = models.TextField(blank=True, null=True)
    pending_started_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PostMedia(models.Model):
    media_url = models.CharField(max_length=300)
    media_type = models.CharField(max_length=50, choices=MediaTypeChoices)
    order = models.IntegerField(default=0)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_media')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
