from celery import shared_task
from .models import PaymentTransaction
from datetime import datetime, timezone, timedelta
from django.conf import settings

@shared_task
def mark_expired_payment_transaction():
    valid_time = datetime.now(timezone.utc) - timedelta(minutes=settings.TRANSACTION_VALIDITY_PERIOD)
    PaymentTransaction.objects.filter(status='PENDING', created_at__lt=valid_time).update(status='EXPIRED')