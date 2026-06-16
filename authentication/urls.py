from django.urls import path
from .views import RegistrationView, LoginView, GoogleLoginView

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('google/', GoogleLoginView.as_view(), name='google_login')
]