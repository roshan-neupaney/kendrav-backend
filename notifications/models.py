from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

NotificationTypeChoices = [
    ('post_published', 'Post Published'),
    ('post_failed', 'Post Failed'),
    ('new_comment', 'New Comment'),
    ('scheduled_reminder', 'Scheduled Reminder'),
    ('queue_limit', 'Queue Limit'),
    ('channel_expired', 'Channel Expired'),
    ('team_invite', 'Team Invite'),
    ('post_approval', 'Post Approval'),
    ('analytics_summary', 'Analytics Summary'),
    ('billing', 'Billing'),
    ('announcements', 'Announcements')
]

class Notification(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    image_url = models.CharField(max_length=300, blank=True, null=True)
    action_type = models.CharField(max_length=100, blank=True, null=True)
    redirect_url = models.CharField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class NotificationPreference(models.Model):
    notification_type = models.CharField(max_length=100, choices=NotificationTypeChoices)
    is_permitted = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='workspace_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notification_users')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)