from django.urls import path
from .views import (
    UserNotificationView,
    UserNotificationReadView,
    UserNotificationReadAllView,
    RegisterFCMToken,
    UnRegisterFCMToken,
    ToggleTokenSubscriptionToTopicView
)

urlpatterns = [
    path("", UserNotificationView.as_view(), name="user-notification"),
    path(
        "<int:notification_id>/read/",
        UserNotificationReadView.as_view(),
        name="user-notification-read",
    ),
    path(
        "<int:notification_id>/read-all/",
        UserNotificationReadAllView.as_view(),
        name="user-notification-read-all",
    ),
    path("fcm-token/register/", RegisterFCMToken.as_view(), name="fcm-token-register"),
    path(
        "fcm-token/unregister/",
        UnRegisterFCMToken.as_view(),
        name="fcm-token-unregister",
    ),
    path(
        "topic/toggle-subscription/",
        ToggleTokenSubscriptionToTopicView.as_view(),
        name="topic-toggle-subscription",
    ),
]
