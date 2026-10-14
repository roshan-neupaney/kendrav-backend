from django.urls import path

from .views import PaymentInitializeView, PaymentVerificationView

urlpatterns = [
    path("initiate/", PaymentInitializeView.as_view(), name="initiate-payment"),
    path("verify/", PaymentVerificationView.as_view(), name="verify-payment"),
]
