from django.urls import path
from .views import (
    WorkspaceView,
    WorkspaceWithIdView,
    WorkspaceMemeberView,
    WorkspaceMemberInviteView,
    MemberInviteAcceptView,
    MemberInviteDeclineView,
    WorkspaceMemberWithIdView,
    WorkspaceMemberLeaveView,
)

urlpatterns = [
    path("", WorkspaceView.as_view(), name="workspace"),
    path(
        "<str:workspace_id>/", WorkspaceWithIdView.as_view(), name="workspace-with-id"
    ),
    path("members/", WorkspaceMemeberView.as_view(), name="workspace-members"),
    path(
        "member/invite/",
        WorkspaceMemberInviteView.as_view(),
        name="workspace-member-invite",
    ),
    path(
        "member/accept-invite/",
        MemberInviteAcceptView.as_view(),
        name="member-accept-invite",
    ),
    path(
        "member/decline-invite/",
        MemberInviteDeclineView.as_view(),
        name="member-decline-invite",
    ),
    path(
        "member/<int:member_id>/",
        WorkspaceMemberWithIdView.as_view(),
        name="member-with-id",
    ),
    path(
        "member/leave",
        WorkspaceMemberLeaveView.as_view(),
        name="member-leave",
    ),
]
