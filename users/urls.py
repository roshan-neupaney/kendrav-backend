from django.urls import path
from .views import UserView

urlpatterns = [
    path("me/<str:workspace_id>/", UserView.as_view(), name="user-me"),
]
