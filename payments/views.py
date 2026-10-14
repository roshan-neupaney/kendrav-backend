from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentMethod, PaymentTransaction
from .payment_handler import payment_handler
from .serializers import PaymentInitializeSerializer, PaymentTransactionSerializer


class PaymentInitializeView(APIView):
    def post(self, request):
        serializer = PaymentInitializeSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            payment_method_id = serializer.validated_data.get("payment_method_id")
            subscription_id = serializer.validated_data.get("subscription_id")
            transaction_uuid = serializer.validated_data.get("transaction_uuid")
            idempotency_key = cache.get(f"idempotency_{transaction_uuid}", False)

            if idempotency_key:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Duplicate request",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Duplicate request",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment_transaction = PaymentTransaction.objects.filter(
                transaction_uuid=transaction_uuid
            ).exists()

            if payment_transaction:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Duplicate request",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cache.set(f"idempotency_{transaction_uuid}", True, timeout=86400)

            payload = {
                "redirect_url": serializer.validated_data.get("redirect_url"),
                "website_url": serializer.validated_data.get("website_url"),
                "transaction_uuid": transaction_uuid,
            }

            payment_method = PaymentMethod.objects.filter(id=payment_method_id).first()
            handler = payment_handler(payment_method.gateway_type)

            result = handler.initiate_payment(
                payload=payload,
                subscription_id=subscription_id,
                user_id=request.user.id,
                payment_method_id=payment_method.id,
            )

            if not result:
                return Response(
                    {
                        "message": "Payment initiation failed",
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                "status": status.HTTP_400_BAD_REQUEST,
            }
        )


class PaymentVerificationView(APIView):
    def post(self, request):
        pidx = request.data.get("pidx", None)

        if not pidx:
            return Response(
                {"message": "pidx is required", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_transaction = (
            PaymentTransaction.objects.select_related("payment_method")
            .filter(payment_idx=pidx)
            .first()
        )

        if not payment_transaction:
            return Response(
                {
                    "message": "Transaction not found",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment_transaction.status == "EXPIRED":
            return Response(
                {
                    "message": "Transaction expired",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        handler = payment_handler(payment_transaction.payment_method.gateway_type)

        result = handler.verify_payment(pidx=pidx)

        serializer = PaymentTransactionSerializer(result.get("data"))

        return Response(
            {
                "message": result.get("message", ""),
                "status": status.HTTP_200_OK
                if result.get("status", False)
                else status.HTTP_500_INTERNAL_SERVER_ERROR,
                "data": serializer.data,
            }
        )
