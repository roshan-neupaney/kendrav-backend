from django.urls import path
from .views import PostView, PostWithIdView, PostPublishView

urlpatterns = [
    path("", PostView.as_view(), name="post"),
    path("<int:post_id>/", PostWithIdView.as_view(), name="post-with-id"),
    path("<int:post_id>/publish/", PostPublishView.as_view(), name="post-publish"),
]
