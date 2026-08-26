from .serializers import UserSerializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.permission import HasWorkspacePermission


class UserView(APIView):
    permission_classes=[HasWorkspacePermission('workspace:can_delete')]
    def get(self, request):
        user = request.user
        serializer = UserSerializers(user)
        return Response(
            {
                "message": "Users fetched successfully.",
                "data": serializer.data,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )
