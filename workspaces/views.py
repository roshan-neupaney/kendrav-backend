from .permission import HasWorkspacePermission, IsWorkspaceMember
from rest_framework.views import APIView
from .serializers import (
    WorkspaceSerializer,
    WorkspaceWithIdSerializer,
    WorkspaceMemeberSerializer,
    WorkspaceMemberInviteSerializer,
    MemberInviteAcceptSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace, WorkspaceMember, WorkspaceMemberInvite
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from django.db import transaction


class WorkspaceView(APIView):
    def get(self, request):
        user = request.user
        user_workspaces = Workspace.objects.filter(
            Q(owner=user) | Q(workspace_members__user_id=user), is_active=True
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


class WorkspaceMemeberView(APIView):
    def get_permissions(self):
        permissions = {
            "GET": [IsAuthenticated(), IsWorkspaceMember()],
        }
        return permissions.get(self.request.method, [IsAuthenticated(), IsWorkspaceMember()])

    def get(self, request):
        workspace_id = request.header.get("workspaceId", "")
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
        return permissions.get(self.request.method, [IsAuthenticated(), IsWorkspaceMember()])

    def post(self, request):
        serializer = WorkspaceMemberInviteSerializer(
            data=request.data, context={"user": request.user}
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

    def get(self, request):
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
        return permissions.get(self.request.method, [IsAuthenticated(), IsWorkspaceMember()])

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
