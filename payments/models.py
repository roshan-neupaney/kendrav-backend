from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

'COMPLETE | PENDING | FAILURE | FULL_REFUND | PARTIAL_REFUND | AMBIGUOUS | NOT_FOUND | CANCELED'
StatusChoices = [
    ("COMPLETE", "COMPLETE"),
    ("PENDING", "PENDING"),
    ("FAILURE", "FAILURE"),
    ("FULL_REFUND", "FULL_REFUND"),
    ("PARTIAL_REFUND", "PARTIAL_REFUND"),
    ("AMBIGUOUS", "AMBIGUOUS"),
    ("NOT_FOUND", "NOT_FOUND"),
    ("CANCELED", "CANCELED"),
]

class PaymentMethod(models.Model):
    title = models.CharField(max_length=100)
    logo = models.CharField(max_length=300, blank=True, null=True)
    config = models.JSONField(default=dict, blank=True)
    gateway_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PaymentHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_payment_histories')
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.SET_NULL, null=True, related_name='payment_histories')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='payment_method_histories')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_uuid = models.CharField(max_length=100, blank=True, unique=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default='PENDING', choices=StatusChoices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)