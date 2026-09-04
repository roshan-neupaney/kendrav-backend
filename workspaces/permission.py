from rest_framework.permissions import BasePermission
from workspaces.models import WorkspaceMember, RolePermission


class IsWorkspaceMember(BasePermission):
    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id")
        user = request.user
        if not workspace_id:
            return False
        workspace_member = WorkspaceMember.objects.filter(
            user=user, workspace_id=workspace_id
        ).first()

        return bool(workspace_member)


def HasWorkspacePermission(required_permission):
    class _HasWorkspacePermission(BasePermission):
        def has_permission(self, request, view):
            workspace_id = view.kwargs.get("workspace_id")
            user = request.user
            member_role_permissions = []
            workspace_member = (
                WorkspaceMember.objects.prefetch_related(
                    "member_permissions", "member_roles"
                )
                .filter(workspace_id=workspace_id, user=user)
                .first()
            )

            if workspace_member is None:
                return False

            member_roles = workspace_member.member_roles.all().values_list(
                "role_id", flat=True
            )

            role_permissions = RolePermission.objects.select_related(
                "permission"
            ).filter(role_id__in=member_roles)

            role_permissions = list(role_permissions)

            for item in role_permissions:
                member_role_permissions.append(item.permission.title)

            member_permissions = workspace_member.member_permissions.select_related(
                "permission"
            ).all()
            member_permissions = list(member_permissions)

            for item in member_permissions:
                title = item.permission.title
                is_revoked = item.is_revoked
                if title in member_role_permissions and is_revoked:
                    member_role_permissions.remove(title)
                elif not title in member_role_permissions and not is_revoked:
                    member_role_permissions.append(title)

            return required_permission in member_role_permissions

    return _HasWorkspacePermission
