from celery import shared_task
from .models import NotificationPreference, Notification
from users.models import UserFcmToken
from firebase_admin import messaging
from workspaces.models import Workspace
import logging
from datetime import datetime, timedelta, timezone
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)

notification_types = [
    "post_published",
    "post_failed",
    "new_comment",
    "scheduled_reminder",
    "queue_limit",
    "channel_expired",
    "team_invite",
    "post_approval",
    "analytics_summary",
    "billing",
    "announcements",
]


@shared_task
def send_notification_by_topic(topic, notification_id):
    notification = Notification.objects.filter(id=notification_id).first()

    if not notification:
        return

    try:
        messaging.send(
            messaging.Message(
                topic=topic,
                notification=messaging.Notification(
                    title=notification.title, body=notification.body
                ),
            )
        )
    except Exception as e:
        logger.error(f"Failed to send notification to topic {topic}: {e}")


@shared_task
def subscribe_to_all_topic(workspace_slug, user, fcm_token):

    user_notification_preferences = NotificationPreference.objects.filter(
        user=user, is_permitted=True
    )
    user_preferred_topics = user_notification_preferences.values_list(
        "notification_type", flat=True
    )

    for topic in user_preferred_topics:
        workspace_topic = f"{workspace_slug}_{topic}"

        result = messaging.subscribe_to_topic([fcm_token], workspace_topic)
        if result.failure_count > 0:
            for error in result.errors:
                if error.reason == "INVALID_REGISTRATION":
                    UserFcmToken.objects.filter(fcm_token=fcm_token).update(
                        is_active=False
                    )
                    return
                else:
                    logger.error(f"Failed to subscribe: {error.reason}")


@shared_task
def unsubscribe_from_all_topic(workspace_slug, fcm_tokens):
    for topic in notification_types:
        workspace_topic = f"{workspace_slug}_{topic}"
        try:
            messaging.unsubscribe_from_topic(fcm_tokens, workspace_topic)
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {workspace_topic}: {e}")


@shared_task
def unsubscribe_inactive_tokens_from_topics():
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    user_fcm_token = UserFcmToken.objects.filter(
        Q(updated_at__lt=cutoff) | Q(is_active=False)
    )

    users = list(user_fcm_token.values_list("user", flat=True))

    workspace_slugs = list(
        Workspace.objects.filter(workspace_members__user__in=users).values_list(
            "slug_url", flat=True
        )
    )

    existing_token_list = list(user_fcm_token.all().values_list("fcm_token", flat=True))

    if len(existing_token_list) > 0:
        for slug in workspace_slugs:
            unsubscribe_from_all_topic(
                workspace_slug=slug,
                fcm_tokens=existing_token_list,
            )

        user_fcm_token.delete()


def subscribe_to_topic(fcm_tokens, topic):
    result = messaging.subscribe_to_topic(fcm_tokens, topic)
    if result.failure_count > 0:
        for error in result.errors:
            logger.error(f"Failed to subscribe {result.failure_count} token{'s' if result.failure_count > 1 else ''}: {error.reason}")


def unsubscribe_to_topic(fcm_tokens, topic):
    try:
        messaging.unsubscribe_from_topic(fcm_tokens, topic)
    except Exception as e:
        logger.error(f"Failed to unsubscribe from {topic}: {e}")


@shared_task
def toggle_topic_subscription(user_id, type):
    user = User.objects.prefetch_related(
        "user_workspaces", "notification_preferences", "fcm_tokens"
    ).filter(id=user_id).first()

    preferred_notification = user.notification_preferences.filter(
        notification_type=type
    ).first()

    user_workspaces = list(user.user_workspaces.all())

    workspace_slugs = [uw.workspace.slug_url for uw in user_workspaces]

    user_fcm_tokens = list(user.fcm_tokens.filter(is_active=True).values_list("fcm_token", flat=True))

    if not len(user_fcm_tokens) > 0:
        return

    for slug in workspace_slugs:
        topic = f"{slug}_{preferred_notification.notification_type}"
        if preferred_notification.is_permitted:
            unsubscribe_to_topic(fcm_tokens=user_fcm_tokens, topic=topic)
            preferred_notification.is_permitted = False
        else:
            subscribe_to_topic(fcm_tokens=user_fcm_tokens, topic=topic)
            preferred_notification.is_permitted = True
        
    preferred_notification.save()