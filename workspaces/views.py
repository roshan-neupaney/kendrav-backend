from .permission import HasWorkspacePermission, IsWorkspaceMember
from rest_framework.views import APIView
from .serializers import WorkspaceSerializer, WorkspaceWithIdSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace
from django.db.models import Q
from .utils import generate_workspace_slug

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
                "message": "Workspaces retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    
    def post(self, request):
        user = request.user
        data = request.data
        data['slug_url'] = generate_workspace_slug(request.data['title'], '')
        serializer = WorkspaceSerializer(user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            result = serializer.save()
            print(result)
            return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Workspace created successfully",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )


class WorkspaceWithIdView(APIView):
    permission_classes = [IsWorkspaceMember]

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