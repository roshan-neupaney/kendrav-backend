import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from subscriptions.models import Subscription
from users.models import UserSubscription

from .models import PaymentMethod, PaymentTransaction
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

User = get_user_model()


def payment_handler(type):
    handlers = {"khalti": KhaltiHandler}
    return handlers.get(type)()


class KhaltiHandler:
    base_url = settings.KHALTI_URL

    def initiate_payment(
        self,
        payload,
    ):
        
        total_amount = payload.get('total_amount')
        amount = int(total_amount * 100)
        transaction_uuid = payload.get("transaction_uuid")
        data = {
            "return_url": payload.get("redirect_url"),
            "website_url": payload.get("website_url"),
            "amount": amount,
            "purchase_order_id": transaction_uuid,
            "purchase_order_name": payload.get("purchase_order_name"),
        }

        headers = {
            "Authorization": f"Key {settings.KHALTI_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                f"{self.base_url}/epayment/initiate/", json=data, headers=headers
            )

            if response.ok:
                res_json = response.json()
                pidx = res_json.get("pidx", None)
                if pidx:
                    return {
                        "payment_idx": pidx,
                        "payment_url": res_json.get("payment_url"),
                    }
        except Exception as e:
            logger.error(f"Failed to initiate payment {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
    )
    def verify_payment(self, pidx):
        try:
            payment_transaction = PaymentTransaction.objects.filter(
                payment_idx=pidx
            ).first()

            headers = {
                "Authorization": f"Key {settings.KHALTI_API_KEY}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                f"{self.base_url}/epayment/lookup/",
                json={"pidx": pidx},
                headers=headers,
            )
            if response.ok:
                res_json = response.json()
                status = {
                    "Completed": "COMPLETED",
                    "Pending": "PENDING",
                    "Refunded": "FULL_REFUNDED",
                    "Partially Refunded": "PARTIAL_REFUNDED",
                    "Expired": "EXPIRED",
                    "User canceled": "CANCELED",
                }
                payment_transaction.status = status.get(res_json.get("status"))
                payment_transaction.gateway_response = res_json
                payment_transaction.save()

                if payment_transaction.status == "COMPLETED":
                    user = User.objects.filter(id=payment_transaction.user).first()
                    subscription = Subscription.objects.filter(
                        id=payment_transaction.subscription
                    ).first()
                    UserSubscription.objects.filter(user=user, is_active=True).update(
                        is_active=False
                    )

                    start_date = datetime.now(timezone.utc)
                    end_date = datetime.now(timezone.utc) + timedelta(
                        days=subscription.duration_days
                    )

                    UserSubscription.objects.create(
                        user=user,
                        subscription=subscription,
                        start_date=start_date,
                        end_date=end_date,
                        payment_transaction=payment_transaction,
                    )

                return {"status": True, "data": payment_transaction}
            else:
                return {"status": False, "data": payment_transaction}

        except Exception as e:
            logger.error(f"Failed to verify payment: {e}")
            # return None
