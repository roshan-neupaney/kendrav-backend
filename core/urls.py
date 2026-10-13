from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("authentication.urls")),
    path("accounts/", include("allauth.urls")),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/workspace/", include("workspaces.urls")),
    path("api/v1/workspace/", include("channels.urls")),
    path("api/v1/channel/", include("channels.urls")),
    path("api/v1/workspace/<int:workspace_id>/post/", include("posts.urls")),
    path("api/v1/media/presigned-url/", include("medias.urls")),
    path("api/v1/notification/", include("notifications.urls")),
    path("api/v1/payment/", include("payments.urls")),
]
