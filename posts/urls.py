from django.urls import path
from .views import PostView, PostWithIdView, PostPublishView, PostApprovalRequestView

urlpatterns = [
    path("", PostView.as_view(), name="post"),
    path("<int:post_id>/", PostWithIdView.as_view(), name="post-with-id"),
    path("<int:post_id>/publish/", PostPublishView.as_view(), name="post-publish"),
    path("<int:post_id>/approval-request/", PostApprovalRequestView.as_view(), name="approval-request"),
]
