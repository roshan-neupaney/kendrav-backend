from django.urls import path
from .views import PostView, PostWithIdView

urlpatterns = [
    path("", PostView.as_view(), name="post"),
    path("<int:post_id>/", PostWithIdView.as_view(), name="post-with-id"),
]
