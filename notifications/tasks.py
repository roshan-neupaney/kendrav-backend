from celery import shared_task
from .models import NotificationPreference, Notification
from users.models import UserFcmToken
from firebase_admin import messaging


@shared_task
def send_notification(notification_type, users, notification_id):
    preferred_users = NotificationPreference.objects.filter(
        notification_type=notification_type,
        is_permitted=True,
        user__in=users,
        is_active=True,
    ).values_list("user", flat=True)

    notification = Notification.objects.filter(id=notification_id).first()

    fcm_tokens = UserFcmToken.objects.filter(
        user__in=preferred_users, is_active=True
    ).values_list("fcm_token", flat=True)

    if not len(fcm_tokens) > 0:
        return

    message = messaging.MulticastMessage(
        tokens=fcm_tokens,
        notification=messaging.Notification(
            title=notification.title, body=notification.body
        ),
    )
    response = messaging.send_each_for_multicast(message)

    print(response)
