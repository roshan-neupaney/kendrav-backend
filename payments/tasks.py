from celery import shared_task
from .models import PaymentTransaction

@shared_task
def delete_expired_payment_transaction(transaction_id):
    PaymentTransaction.objects.delete(id=transaction_id, status='PENDING')