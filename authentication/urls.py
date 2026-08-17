from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    GoogleLoginView,
    LogoutView,
    LogoutAllView,
    LogoutDeviceView,
    ActiveSessionView,
    ChangePasswordView,
    ChangePasswordOTPView,
    ForgotPasswordView,
    ResetPasswordView,
    RefreshTokenView
)

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
    path("token-refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout/all-devices/", LogoutAllView.as_view(), name="logout-all"),
    path("logout/device/", LogoutDeviceView.as_view(), name="logout-device"),
    path("active-session/", ActiveSessionView.as_view(), name="active-session"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("change-password-otp/", ChangePasswordOTPView.as_view(), name="change-password-otp"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
