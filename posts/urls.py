from django.urls import path
from .views import PostView, PostWithIdView, PostPublishView, PostApprovalRequestView, PostApproveView, PostRejectView

urlpatterns = [
    path("", PostView.as_view(), name="post"),
    path("<int:post_id>/", PostWithIdView.as_view(), name="post-with-id"),
    path("<int:post_id>/publish/", PostPublishView.as_view(), name="post-publish"),
    path("<int:post_id>/approval-request/", PostApprovalRequestView.as_view(), name="approval-request"),
    path("<int:post_id>/approve/", PostApproveView.as_view(), name="post-approve"),
    path("<int:post_id>/reject/", PostRejectView.as_view(), name="post-reject"),
]
