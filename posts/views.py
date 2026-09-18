from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from workspaces.permission import IsWorkspaceMember, HasWorkspacePermission
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .serializers import PostSerializer


class PostView(APIView):
    def get_permissions(self):
        permissions = {
            "POST": [
                IsAuthenticated(),
                HasWorkspacePermission("post:can_create")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def get(self, request, workspace_id):

        created_by= request.query_params.get('created_by')
        post_status= request.query_params.get('status')
        start_date= request.query_params.get('start_date')
        end_date= request.query_params.get('end_date')
        sort_by= request.query_params.get('sort_by')

        posts = Post.objects.filter(workspace=workspace_id, is_active=True)

        if created_by:
            posts.filter(created_by=created_by)
        if post_status:
            posts.filter(status=post_status)
        if start_date and end_date:
            posts.filter(published_at__gt=start_date, published_at__lt=end_date)

        serializer = PostSerializer(posts, many=True)

        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Posts retrived successfully",
                "data": serializer.data,
            }
        )

    def post(self, request, workspace_id):
        serailzer = PostSerializer(
            data=request.data, context={"workspace_id": workspace_id, 'request': request}
        )

        if serailzer.is_valid(raise_exception=True):
            serailzer.save()
            return Response(
                {
                    "message": "Post created esuccessfully",
                    "status": status.HTTP_200_OK,
                    "data": serailzer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": serailzer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
