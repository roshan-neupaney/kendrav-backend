from .permission import HasWorkspacePermission, IsWorkspaceMember
from rest_framework.views import APIView
from .serializers import (
    WorkspaceSerializer,
    WorkspaceWithIdSerializer,
    WorkspaceMemeberSerializer,
    WorkspaceMemberInviteSerializer,
    MemberInviteAcceptSerializer,
    WorkspaceRoleSerializer,
    WorkspaceMemberRoleSerializer,
    RolePermissionSerializer,
    WorkspaceMemberPermissionSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace, WorkspaceMember, WorkspaceMemberInvite, Role
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from django.db import transaction


class WorkspaceView(APIView):
    def get(self, request):
        user = request.user
        user_workspaces = Workspace.objects.filter(
            Q(owner=user) | Q(workspace_members__user_id=user),
            workspace_members__is_active=True,
            is_active=True,
        ).distinct()

        serializer = WorkspaceSerializer(user_workspaces, many=True)
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Workspaces Retrieved Successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = WorkspaceSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "status": status.HTTP_201_CREATED,
                    "message": "Workspace Created Successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class WorkspaceWithIdView(APIView):
    def get_permissions(self):
        permissions = {
            "PATCH": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_update")(),
            ],
            "DELETE": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_delete")(),
            ],
            "GET": [IsAuthenticated(), IsWorkspaceMember()],
        }
        return permissions[self.request.method]

    def get(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).first()
        if not workspace:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Workspace not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = WorkspaceWithIdSerializer(workspace)
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Workspace retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).first()

        if not workspace:
            return Response({"message": "Workspace not found"}, status=404)

        serializer = WorkspaceWithIdSerializer(
            workspace, data=request.data, partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "data": serializer.data,
                    "message": "Workspace Updated Successfully",
                }
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).first()

        if not workspace:
            return Response({"message": "Workspace not found"}, status=404)
        workspace.is_active = False
        workspace.save()
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Workspace Deleted Successfully",
            }
        )


class WorkspaceMemberView(APIView):
    def get_permissions(self):
        permissions = {
            "GET": [IsAuthenticated(), IsWorkspaceMember()],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def get(self, request, workspace_id):
        workspace_member = WorkspaceMember.objects.prefetch_related(
            "member_roles__role", "member_permissions__permission", "user__profile"
        ).filter(is_active=True, workspace=workspace_id)

        serializer = WorkspaceMemeberSerializer(workspace_member, many=True)

        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Workspace members retrived successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceMemberInviteView(APIView):
    def get_permissions(self):
        permissions = {
            "POST": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_invite_members")(),
            ],
            "GET": [IsAuthenticated()],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def post(self, request, workspace_id):
        serializer = WorkspaceMemberInviteSerializer(
            data=request.data,
            context={"user": request.user, "workspace_id": workspace_id},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "status": status.HTTP_201_CREATED,
                    "message": "Invitation Sent Successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request, workspace_id):
        token = request.headers.get("token", "")
        if not token:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": ["Token is required"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invite = WorkspaceMemberInvite.objects.filter(token=token).first()
        if not invite:
            return Response({"message": "Invitation not found"}, status=404)

        serializer = WorkspaceMemberInviteSerializer(invite)
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Invitation retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class MemberInviteAcceptView(APIView):
    def post(self, request):
        serializer = MemberInviteAcceptSerializer(
            data=request.data, context={"user": request.user}
        )

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                serializer.save()
                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Invitation Accepted",
                    },
                    status=status.HTTP_200_OK,
                )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class MemberInviteDeclineView(APIView):
    def post(self, request):
        serializer = MemberInviteAcceptSerializer(
            data=request.data, context={"user": request.user}
        )

        if serializer.is_valid(raise_exception=True):
            member_invite = serializer.validated_data["member_invite"]
            member_invite.status = "declined"
            member_invite.save()
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Invitation Declined",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class WorkspaceMemberWithIdView(APIView):
    def get_permissions(self):
        permissions = {
            "DELETE": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_delete_members")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def delete(self, request, member_id):

        member = WorkspaceMember.objects.filter(id=member_id).first()

        if member is None:
            return Response(
                {
                    "message": "Member not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.is_active = False
        member.save()

        return Response(
            {
                "message": "Member Removed Successfully",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceMemberLeaveView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request):
        workspace_id = request.headers.get("workspaceId", "")

        workspace = Workspace.objects.get(id=workspace_id)

        member = WorkspaceMember.objects.filter(
            is_active=True, workspace=workspace_id, user=request.user
        ).first()

        is_owner = workspace.owner == request.user

        other_members = (
            WorkspaceMember.objects.filter(is_active=True, workspace=workspace_id)
            .exclude(user=request.user)
            .exists()
        )

        if is_owner and other_members:
            return Response(
                {
                    "message": [
                        "Transfer ownership or delete all workspace members first"
                    ],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.is_active = False
        member.save()

        return Response(
            {
                "message": "Successfully left the workspace",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceRoleView(APIView):
    def get_permissions(self):
        permissions = {
            "POST": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_create_roles")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def get(self, request):
        workspace_id = request.headers.get("workspaceId")
        roles = Role.objects.filter(workspace=workspace_id)

        serializer = WorkspaceRoleSerializer(roles, many=True)

        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Roles Retrieved Successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = WorkspaceRoleSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                {
                    "status": status.HTTP_201_CREATED,
                    "message": "Role created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class WorkspaceRoleWithIdView(APIView):
    def get_permissions(self):
        permissions = {
            "PATCH": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_update_roles")(),
            ],
            "DELETE": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_delete_roles")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def get(self, request, role_id):
        role = Role.objects.filter(id=role_id).first()

        if role is None:
            return Response(
                {"status": status.HTTP_400_BAD_REQUEST, "message": ["Role not found"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WorkspaceRoleSerializer(role)

        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Role Retrieved Successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, role_id):
        role = Role.objects.filter(id=role_id).first()

        if role is None:
            return Response(
                {"status": status.HTTP_400_BAD_REQUEST, "message": ["Role not found"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WorkspaceRoleSerializer(
            role, data=request.data, context={"request": request}, partial=True
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Role updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, role_id):
        role = Role.objects.filter(id=role_id).first()

        if role is None:
            return Response(
                {"status": status.HTTP_400_BAD_REQUEST, "message": ["Role not found"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role.delete()

        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Role deleted successfully",
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceMemberRoleView(APIView):
    def get_permissions(self):
        permissions = {
            "POST": [
                IsAuthenticated(),
                HasWorkspacePermission("workspace:can_assign_roles")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def post(self, request, member_id):
        serializer = WorkspaceMemberRoleSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(member_id=member_id)
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Member roles updated successfully",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class WorkspaceMemberPermissionView(APIView):
    permission_classes = [
        IsAuthenticated,
        HasWorkspacePermission("workspace:can_assign_member_permissions"),
    ]

    def post(self, request, member_id):
        serializer = WorkspaceMemberPermissionSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(member_id=member_id)
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Member permissions updated successfully",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class RolePermissionView(APIView):
    permission_classes = [
        IsAuthenticated,
        HasWorkspacePermission("workspace:can_assign_role_permissions"),
    ]

    def post(self, request, role_id):
        serializer = RolePermissionSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(role_id=role_id)
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Role permissions updated successfully",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

