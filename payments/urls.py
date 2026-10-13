from django.urls import path

from .views import PaymentInitializeView

urlpatterns = [
    path("initiate/", PaymentInitializeView.as_view(), name="initiate-payment"),
]
