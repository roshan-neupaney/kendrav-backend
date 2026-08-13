from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    GoogleLoginView,
    LogoutView,
    LogoutAllView,
    LogoutDeviceView,
    ActiveSessionView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
    path("token-refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout/all-devices/", LogoutAllView.as_view(), name="logout"),
    path("logout/device/", LogoutDeviceView.as_view(), name="logout"),
    path("active-session/", ActiveSessionView.as_view(), name="logout"),
]
