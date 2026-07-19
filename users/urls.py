from django.urls import path
from .views import UserView

urlpatterns = [
    path("user-profile/", UserView.as_view(), name="user-profile"),
]
