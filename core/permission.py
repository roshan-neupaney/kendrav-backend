from rest_framework import permissions
from workspaces.models import WorkspaceMember

class IsWorkspaceMember(permissions.BasePermission):
    def has_permission(self, request, view):
        workspace_id = view.kwargs.get('workspace_id')
        user = request.user
        if not workspace_id:
            return False
        workspace_member = WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id).first()

        return bool(workspace_member)

class HasWorkspacePermission(permissions.BasePermission):
    def __init__(self, required_permission):
        self.required_permission = required_permission
        
    def has_permission(self, request, view):
        workspace_id = view.kwargs.get('workspace_id')
        user = request.user
        workspace_member = WorkspaceMember.objects.filter(user=user, workspace=workspace_id).exists()

        return bool(workspace_member)