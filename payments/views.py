from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentMethod
from .payment_handler import payment_handler
from .serializers import PaymentInitializeSerializer
from subscriptions.models import Subscription


class PaymentInitializeView(APIView):
    def post(self, request):
        serializer = PaymentInitializeSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            payment_method_id = serializer.validated_data.get("payment_method_id")
            subscription_id = serializer.validated_data.get("subscription_id")

            payload = {
                "redirect_url": serializer.validated_data.get("redirect_url"),
                "website_url": serializer.validated_data.get("website_url"),
                "transaction_uuid": serializer.validated_data.get("transaction_uuid"),
            }
            
            payment_method = PaymentMethod.objects.filter(id=payment_method_id).first()
            handler = payment_handler(payment_method.gateway_type)

            result = handler.initiate_payment(
                payload=payload,
                subscription_id=subscription_id,
                user_id=request.user.id,
                payment_method_id=payment_method.id,
            )

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "data": result,
                    "message": "Payment initiated successfully",
                },
                status=status.HTTP_200_OK,
            )
        
        return Response(
            {
                "message": serializer.error_messages,
                "status": status.HTTP_400_BAD_REQUEST
            }
        )
