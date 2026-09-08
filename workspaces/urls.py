from django.urls import path
from .views import WorkspaceView, WorkspaceWithIdView, WorkspaceMemeberView, WorkspaceMemberInviteView, MemberInviteAcceptView, MemberInviteDeclineView

urlpatterns = [
    path("", WorkspaceView.as_view(), name="workspace"),
    path("<str:workspace_id>/", WorkspaceWithIdView.as_view(), name="workspace-with-id"),
    path("<str:workspace_id>/members/", WorkspaceMemeberView.as_view(), name="workspace-with-id"),
    path("<str:workspace_id>/member/invite/", WorkspaceMemberInviteView.as_view(), name="workspace-member-invite"),
    path("member/accept-invite/", MemberInviteAcceptView.as_view(), name="member-accept-invite"),
    path("member/decline-invite/", MemberInviteDeclineView.as_view(), name="member-decline-invite"),
]