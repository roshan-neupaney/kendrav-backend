from django.urls import path
from .views import SignedUploadCredentialsView

urlpatterns = [
    path("", SignedUploadCredentialsView.as_view(), name="signed-url")
]