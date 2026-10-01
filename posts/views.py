from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from workspaces.permission import IsWorkspaceMember, HasWorkspacePermission
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .serializers import PostSerializer, PostPublishSerializer
from .pagination import StandardCursorPagination
from datetime import datetime, timezone
from django.db import transaction


class PostView(APIView):
    pagination_class = StandardCursorPagination

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

        sortable_fields = ["created_at", "updated_at", "published_at", "schedule_time"]

        created_by = request.query_params.get("created_by", "")
        created_by_list = created_by.split(",") if created_by else []
        post_status = request.query_params.get("status")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        sort_by = request.query_params.get("sort_by")

        posts = Post.objects.prefetch_related("post_medias").filter(
            workspace=workspace_id, is_active=True
        )

        if len(created_by_list) > 0:
            posts = posts.filter(created_by__in=created_by_list)

        if post_status:
            posts = posts.filter(status=post_status)

        if start_date and end_date:
            start_date_dt = datetime.fromisoformat(start_date)
            end_date_dt = datetime.fromisoformat(end_date)
            if start_date_dt > end_date_dt:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "End date cannot be past of start date",
                    }
                )
            posts = posts.filter(
                published_at__gt=start_date_dt, published_at__lt=end_date_dt
            )

        if sort_by and sort_by in sortable_fields:
            posts = posts.order_by(sort_by)

        paginator = self.pagination_class()
        paginated_post = paginator.paginate_queryset(posts, request=request, view=self)

        serializer = PostSerializer(paginated_post, many=True)

        result = paginator.get_paginated_response(serializer.data)
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Posts retrived successfully",
                "data": result.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, workspace_id):
        serializer = PostSerializer(
            data=request.data,
            context={"workspace_id": workspace_id, "request": request},
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save(created_by=request.user)
            return Response(
                {
                    "message": "Post created successfully",
                    "status": status.HTTP_201_CREATED,
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class PostWithIdView(APIView):
    def get_permissions(self):
        permissions = {
            "PATCH": [
                IsAuthenticated(),
                HasWorkspacePermission("post:can_update")(),
            ],
            "DELETE": [
                IsAuthenticated(),
                HasWorkspacePermission("post:can_delete")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def get(self, request, workspace_id, post_id):
        post = Post.objects.filter(id=post_id).first()

        if not post:
            return Response(
                {"message": "Post not found", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PostSerializer(post)

        return Response(
            {
                "message": "Post retrived successfully",
                "status": status.HTTP_200_OK,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, workspace_id, post_id):
        post = Post.objects.filter(id=post_id, is_active=True).first()

        if not post:
            return Response(
                {"message": "Post not found", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PostSerializer(
            post,
            data=request.data,
            context={"workspace_id": workspace_id, "request": request},
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save(created_by=request.user)
            return Response(
                {
                    "message": "Post updated successfully",
                    "status": status.HTTP_200_OK,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, workspace_id, post_id):
        post = Post.objects.filter(id=post_id, is_active=True).first()

        if not post:
            return Response(
                {"message": "Post not found", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post.is_active = False
        post.save()

        return Response(
            {
                "message": "Post deleted successfully",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class PostPublishView(APIView):
    def get_permissions(self):
        permissions = {
            "PATCH": [
                IsAuthenticated(),
                HasWorkspacePermission("post:can_publish")(),
            ],
        }
        return permissions.get(
            self.request.method, [IsAuthenticated(), IsWorkspaceMember()]
        )

    def patch(self, request, workspace_id, post_id):
        post = Post.objects.filter(
            workspace_id=workspace_id, id=post_id, is_active=True
        ).first()

        if not post:
            return Response(
                {"message": "Post not found", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if post.status != "draft" and post.status != "scheduled":
            message = ""
            if post.status == "pending":
                message = "Post already publishing"
            elif post.status == "for_approval":
                message = "Approval pending"
            elif post.status == "rejected":
                message = "Publish request rejected"
            else:
                message = "Post already published"

            return Response(
                {
                    "message": message,
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PostPublishSerializer(
            post,
            data=request.data,
            context={"workspace_id": workspace_id, "request": request},
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                serializer.save()
                post_status = request.data.get("post_status")
                message = ""
                if post_status == "draft":
                    message = "Post saved as draft"
                elif post_status == "schedule" or post_status == "my_time":
                    message = "Post scheduled successfully"
                elif post_status == "now":
                    message = "Publishing..."

                return Response(
                    {
                        "message": message,
                        "status": status.HTTP_200_OK,
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class PostApprovalRequestView(APIView):
    def patch(self, request, workspace_id, post_id):
        post = Post.objects.filter(id=post_id, is_active=True).first()
        reqeust_to = request.data.get("reqeust_to")

        allowed_requests = ["schedule", "my_time"]

        if not reqeust_to:
            return Response(
                {
                    "message": ["Request to field is required"],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reqeust_to in allowed_requests:
            return Response(
                {
                    "message": [f"{reqeust_to} is not a valid status"],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not post:
            return Response(
                {"message": ["Post not found"], "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if post.status != "draft" and post.status != "rejected":
            message = ""
            if post.status == "pending":
                message = "Post already publishing"
            elif post.status == "scheduled":
                message = "Post already scheduled"
            elif post.status == "for_approval":
                message = "Post already sent for approval"
            else:
                message = "Post already published"
            return Response(
                {
                    "message": [message],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reqeust_to == "schedule":
            schedule_date_time = post.schedule_date_time
            if not schedule_date_time:
                return Response(
                    {
                        "message": ["Schedule date time is required"],
                        "status": status.HTTP_400_BAD_REQUEST,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            now = datetime.now(timezone.utc)
            if schedule_date_time < now:
                return Response(
                    {
                        "message": ["Schedule date time cannot be in past"],
                        "status": status.HTTP_400_BAD_REQUEST,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        post.status = "for_approval"
        post.post_request_to = reqeust_to
        post.save()

        return Response(
            {
                "message": "Request sent for approval",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class PostApproveView(APIView):
    def patch(self, request, workspace_id, post_id):
        post = Post.objects.filter(
            id=post_id, is_active=True, status="for_approval"
        ).first()

        if not post:
            return Response(
                {"message": ["Post not found"], "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_to = post.post_request_to

        serializer = PostPublishSerializer(
            post,
            data={"post_status": request_to},
            context={"workspace_id": workspace_id, "request": request},
            partial=True,
        )

        post.post_request_to = None

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                serializer.save()

                return Response(
                    {
                        "message": "Post approved",
                        "status": status.HTTP_200_OK,
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class PostRejectView(APIView):
    def patch(self, request, workspace_id, post_id):
        remarks = request.data.get("remarks")

        if not remarks:
            return Response(
                {
                    "message": ["Remarks is required"],
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        post = Post.objects.filter(
            id=post_id, is_active=True, status="for_approval"
        ).first()

        if not post:
            return Response(
                {"message": ["Post not found"], "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post.status = "rejected"
        post.save()

        return Response(
            {
                "message": "Request sent for approval",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )
