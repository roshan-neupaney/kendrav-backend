from celery import shared_task
from .models import NotificationPreference, Notification
from users.models import UserFcmToken
from firebase_admin import messaging
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_notification_by_topic(topic, notification_id):
    print(topic)
    notification = Notification.objects.filter(id=notification_id).first()
    
    if not notification:
        return
    
    try:
        resp = messaging.send(
            messaging.Message(
                topic=topic,
                notification=messaging.Notification(
                    title=notification.title, 
                    body=notification.body
                ),
            )
        )
        print('resp', resp)
    except Exception as e:
        logger.error(f"Failed to send notification to topic {topic}: {e}")


@shared_task
def subscribe_to_topic(workspace_slug, user, fcm_token):

    user_notification_preferences = NotificationPreference.objects.filter(
        user=user, is_active=True
    )
    user_preferred_topics = user_notification_preferences.values_list(
        "notification_type", flat=True
    )
    for topic in user_preferred_topics:
        workspace_topic = f"{workspace_slug}_{topic}"
        print(workspace_topic)
        messaging.subscribe_to_topic([fcm_token], workspace_topic)


@shared_task
def unsubscribe_from_topic(workspace_slug, user, fcm_tokens):

    user_notification_preferences = NotificationPreference.objects.filter(
        user=user, is_active=True
    )

    user_preferred_topics = user_notification_preferences.values_list(
        "notification_type", flat=True
    )

    for topic in user_preferred_topics:
        workspace_topic = f"{workspace_slug}_{topic}"
        messaging.unsubscribe_from_topic(fcm_tokens, workspace_topic)
