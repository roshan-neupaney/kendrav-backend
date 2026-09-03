from .permission import HasWorkspacePermission
from rest_framework.views import APIView
from .serializers import WorkspaceSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace
from django.db.models import Q

class WorkspaceView(APIView):
    def get(self, request):
        user = request.user
        user_workspaces = Workspace.objects.filter(Q(owner=user) | Q(workspace_members__user_id = user), is_active=True).distinct()

        serializer = WorkspaceSerializer(user_workspaces, many=True)
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Workspaces retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
