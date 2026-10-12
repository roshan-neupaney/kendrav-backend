import requests
from django.conf import settings


def payment_handler(slug_url):
    handlers = {"khalti": KhaltiHandler}
    return handlers.get(slug_url)()

class KhaltiHandler:
    base_url = f"{settings.KHALTI}epayment/initiate/"

    def initiate_payment(self, payload):
        data={
            "return_url": payload.get('success_url'),
            "website_url": payload.get("website_url"),
            "amount": payload.get("total_amount"),

        }
        response = requests.post(self.base_url, data=payload)

        return response