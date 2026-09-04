from django.urls import path
from .views import WorkspaceView, WorkspaceWithIdView, WorkspaceMemeberView

urlpatterns = [
    path("", WorkspaceView.as_view(), name="workspace"),
    path("<str:workspace_id>/", WorkspaceWithIdView.as_view(), name="workspace-with-id"),
    path("<str:workspace_id>/members/", WorkspaceMemeberView.as_view(), name="workspace-with-id"),
]