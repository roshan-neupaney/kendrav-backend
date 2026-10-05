from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserNotification
from posts.pagination import StandardCursorPagination
from .serializers import UserNotificationSerializer, RegisterFCMTokenSerializer
from users.models import UserFcmToken


class UserNotificationView(APIView):
    pagination_class = StandardCursorPagination

    def get(self, request):
        user_notifications = UserNotification.objects.select_related(
            "notification"
        ).filter(user=request.user)

        paginator = self.pagination_class()
        paginated_user_notification = paginator.paginate_queryset(
            user_notifications, request=request, view=self
        )

        serializer = UserNotificationSerializer(paginated_user_notification, many=True)

        result = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                "message": "User notifications fetched successfully",
                "status": status.HTTP_200_OK,
                "data": result.data,
            },
            status=status.HTTP_200_OK,
        )


class UserNotificationReadView(APIView):
    def post(self, request, notification_id):

        user_notification = UserNotification.objects.filter(
            user=request.user, id=notification_id
        ).first()

        if not user_notification:
            return Response(
                {
                    "message": "Notification not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_notification.is_read = True
        user_notification.save()

        return Response(
            {
                "message": "Notification read successfully",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class UserNotificationReadAllView(APIView):
    def post(self, request):

        user_notifications = UserNotification.objects.filter(
            user=request.user, is_read=False
        )

        user_notifications.update(is_read=True)

        return Response(
            {
                "message": "All notifications read successfully",
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class RegisterFCMToken(APIView):
    def post(self, request):
        serializer = RegisterFCMTokenSerializer(
            data=request.data, context={"user": request.user}
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                {
                    "message": "Device registered successfully",
                    "data": serializer.data,
                    "status": status.HTTP_201_CREATED,
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


class UnRegisterFCMToken(APIView):
    def post(self, request):
        device_id = request.headers.get("deviceId", None)
        user = request.user

        UserFcmToken.objects.filter(user=user, device_id=device_id).delete()
        
        return Response(
            {
                "message": 'Device unregistered successfully',
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )
