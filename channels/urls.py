from django.urls import path
from .views import ChannelView, ChannelWithIdView

urlpatterns = [
    path("", ChannelView.as_view(), name="channel"),
    path("<int:channel_id>/", ChannelWithIdView.as_view(), name="channel-with-id"),
]