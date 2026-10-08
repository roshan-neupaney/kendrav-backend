from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Profile, Preference, UserSubscription
from workspaces.models import (
    Workspace,
    WorkspaceMember,
    Role,
    Permission,
    RolePermission,
    WorkspaceMemberRole,
)
from notifications.models import NotificationPreference
from subscriptions.models import Subscription
from workspaces.utils import generate_workspace_slug

User = get_user_model()

notification_types = {
    "post_published": True,
    "post_failed": True,
    "new_comment": True,
    "scheduled_reminder": True,
    "queue_limit": True,
    "channel_expired": True,
    "team_invite": True,
    "post_approval": True,
    "analytics_summary": True,
    "billing": True,
    "announcements": True,
}


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        full_name = f"{instance.first_name} {instance.last_name}"
        Profile.objects.create(user=instance, full_name=full_name)
        Preference.objects.create(user=instance)
        workspace = Workspace.objects.create(
            owner=instance,
            slug_url=generate_workspace_slug("Personal", ""),
            title="Personal",
            type="personal",
        )
        workspace.slug_url = generate_workspace_slug("Personal", workspace.id)
        workspace.save()
        workspace_member = WorkspaceMember.objects.create(
            user=instance, workspace=workspace
        )
        role = Role.objects.create(workspace=workspace, title="Admin")

        WorkspaceMemberRole.objects.create(workspace_member=workspace_member, role=role)

        permissions = Permission.objects.filter(is_active=True)

        role_permission_instances = [
            RolePermission(role=role, permission=permission)
            for permission in permissions
        ]

        RolePermission.objects.bulk_create(role_permission_instances)

        notification_preference_instances = [
            NotificationPreference(
                user=instance, notification_type=key, is_permitted=value
            )
            for key, value in notification_types.items()
        ]

        NotificationPreference.objects.bulk_create(notification_preference_instances)

        free_plan = Subscription.objects.filter(plan_type="free").first()
        if free_plan:
            UserSubscription.objects.create(user=instance, subscription=free_plan)
