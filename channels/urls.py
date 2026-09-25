from django.urls import path
from .views import (
    ChannelView,
    ChannelWithIdView,
    WorkspaceChannelView,
    WorkspaceChannelWithIdView,
    WorkspaceChannelHealthView,
    ExchangeCodeView
)

urlpatterns = [
    path("", ChannelView.as_view(), name="channel"),
    path("<int:channel_id>/", ChannelWithIdView.as_view(), name="channel-with-id"),
    path(
        "<int:workspace_id>/channel/",
        WorkspaceChannelView.as_view(),
        name="workspace-channel",
    ),
    path(
        "exchange-code/",
        ExchangeCodeView.as_view(),
        name="exchange-code",
    ),
    path(
        "<int:workspace_id>/channel/<int:workspace_channel_id>/",
        WorkspaceChannelWithIdView.as_view(),
        name="workspace-channel-with-id",
    ),
    path(
        "channel/<int:workspace_channel_id>/",
        WorkspaceChannelHealthView.as_view(),
        name="workspace-channel-health",
    ),
]
