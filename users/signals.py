from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Profile, Preference, UserSubscription
from workspaces.models import Workspace, WorkspaceMember
from notifications.models import NotificationPreference
from subscriptions.models import Subscription
from django.utils.text import slugify
from django.utils.crypto import get_random_string

User = get_user_model()

notification_types = [
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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        slug_id = get_random_string(length=6)
        full_name = f"{instance.first_name} {instance.last_name}"
        Profile.objects.create(user=instance, full_name=full_name)
        Preference.objects.create(user=instance)
        workspace = Workspace.objects.create(owner=instance, slug_url=slugify(f"Personal-{slug_id}-{instance.id}"), title='Personal', type='personal')
        WorkspaceMember.objects.create(user=instance, workspace=workspace)
        for notification_type, _ in notification_types:
            NotificationPreference.objects.create(user=instance, notification_type=notification_type, is_permitted=True)
        
        free_plan = Subscription.objects.filter(plan_type='free').first()
        if free_plan:
            UserSubscription.objects.create(user=instance, subscription=free_plan)
