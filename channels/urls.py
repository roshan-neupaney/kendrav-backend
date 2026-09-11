from django.urls import path
from .views import ChannelView

urlpatterns = [
    path("", ChannelView.as_view(), name="channel"),
]