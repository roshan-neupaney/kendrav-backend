from django.urls import path
from .views import ChannelView, ChannelWithIdView, WorkspaceChannelView

urlpatterns = [
    path("", ChannelView.as_view(), name="channel"),
    path("<int:channel_id>/", ChannelWithIdView.as_view(), name="channel-with-id"),
    path(
        "<int:workspace_id>/channel/",
        WorkspaceChannelView.as_view(),
        name="workspace-channel",
    ),
]
