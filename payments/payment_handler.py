import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import PaymentMethod, PaymentTransaction
from subscriptions.models import Subscription

User = get_user_model()


def payment_handler(type):
    handlers = {"khalti": KhaltiHandler}
    return handlers.get(type)()


class KhaltiHandler:
    request_url = f"{settings.KHALTI_URL}/epayment/initiate/"

    def initiate_payment(self, payload, subscription_id, user_id, payment_method_id):
        subscription = Subscription.objects.filter(id=subscription_id).first()
        payment_method = PaymentMethod.objects.filter(id=payment_method_id).first()
        user = User.objects.filter(id=user_id).first()

        total_amount = subscription.price
        amount = total_amount * 10
        transaction_uuid = payload.get("transaction_uuid")
        data = {
            "return_url": payload.get("redirect_url"),
            "website_url": payload.get("website_url"),
            "amount": int(amount),
            "purchase_order_id": transaction_uuid,
            "purchase_order_name": subscription.plan_name,
        }

        headers = {
        "Authorization": f"Key {settings.KHALTI_API_KEY}",
        "Content-Type": "application/json"
    }
        response = requests.post(self.request_url, json=data, headers=headers)

        if response.ok:
            res_json = response.json()
            if res_json.get("pidx", None):
                PaymentTransaction.objects.create(
                    user=user,
                    subscription=subscription,
                    payment_method=payment_method,
                    total_amount=total_amount,
                    transaction_uuid=transaction_uuid,
                )

                return {
                    "idx": res_json.get("pidx"),
                    "payment_url": res_json.get("payment_url"),
                }

        print(response.json())
