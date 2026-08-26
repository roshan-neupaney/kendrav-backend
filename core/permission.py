from rest_framework.permissions import BasePermission
from workspaces.models import WorkspaceMember
from django.core.serializers.json import DjangoJSONEncoder
import json

class IsWorkspaceMember(BasePermission):
    def has_permission(self, request, view):
        workspace_id = view.kwargs.get('workspace_id')
        user = request.user
        if not workspace_id:
            return False
        workspace_member = WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id).first()

        return bool(workspace_member)

def HasWorkspacePermission(required_permission):
    class _HasWorkspacePermission(BasePermission):
        def has_permission(self, request, view):
            print('hello')
            workspace_id = view.kwargs.get('workspace_id')
            user = request.user
            workspace_member = WorkspaceMember.objects.filter(workspace_id = workspace_id, user=user).values_list()
            # roles = workspace_member.member_roles.objects.get()
            print(json.dumps(list(workspace_member), cls=DjangoJSONEncoder))
    return _HasWorkspacePermission
