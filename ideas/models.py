from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

'brainstorming | to-do | in-progress | done | rejected'
StatusChoices = [
    ('brainstorming', 'Brainstorming'),
    ('to_do', 'To Do'),
    ('in_progress', 'In Progress'),
    ('done', 'Done'),
    ('rejected', 'Rejected')
]

class Idea(models.Model):
    title = models.CharField(max_length=225)
    description = models.TextField(blank=True, null=True)
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='ideas')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ideas')
    is_hidden = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default='brainstorming', choices=StatusChoices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class IdeaMedia(models.Model):
    media_url = models.CharField(max_length=300)
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='idea_media')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)