from .permission import HasWorkspacePermission, IsWorkspaceMember
from rest_framework.views import APIView
from .serializers import (
    WorkspaceSerializer,
    WorkspaceWithIdSerializer,
    WorkspaceMemeberSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace, WorkspaceMember
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated


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
        if self.request.method == "PATCH":
            return [IsAuthenticated(), HasWorkspacePermission("workspace:can_update")()]
        elif self.request.method == "DELETE":
            return [IsAuthenticated(), HasWorkspacePermission("workspace:can_delete")()]
        return [IsAuthenticated(), IsWorkspaceMember()]

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
        if self.request.method == "PATCH":
            return [IsAuthenticated(), HasWorkspacePermission("workspace:can_update")()]
        elif self.request.method == "DELETE":
            return [IsAuthenticated(), HasWorkspacePermission("workspace:can_delete")()]
        return [IsAuthenticated(), IsWorkspaceMember()]

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
