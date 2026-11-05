from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentMethod, PaymentTransaction
from .payment_handler import payment_handler
from .serializers import PaymentInitializeSerializer, PaymentTransactionSerializer
from subscriptions.models import Subscription, DurationPackage
from users.models import UserSubscription
from datetime import datetime, timezone, timedelta


class PaymentInitializeView(APIView):
    def post(self, request):
        serializer = PaymentInitializeSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            payment_method_id = serializer.validated_data.get("payment_method_id")
            channel_count = serializer.validated_data.get("channel_count")
            duration_package_id = serializer.validated_data.get("duration_package")
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

            duration_package = (
                DurationPackage.objects.select_related("subscription")
                .filter(id=duration_package_id)
                .first()
            )

            if not duration_package:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Duration package not found",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = duration_package.subscription

            cache.set(f"idempotency_{transaction_uuid}", True, timeout=86400)

            # current_subscription = UserSubscription.objects.filter(
            #     user=request.user, is_active=True
            # ).first()

            # if current_subscription.subscription.plan_type != "free":
            #     is_upgrading = (
            #         current_subscription.subscription.order < subscription.order
            #     )
            #     is_downgrading = (
            #         current_subscription.subscription.order > subscription.order
            #     )

            #     current_duration_package = DurationPackage.objects.filter(
            #         subscription=current_subscription.subscription, is_active=True
            #     ).first()

            #     if not current_duration_package:
            #         return Response(
            #             {
            #                 "status": status.HTTP_400_BAD_REQUEST,
            #                 "message": "Current duration package not found",
            #             },
            #             status=status.HTTP_400_BAD_REQUEST,
            #         )

            #     remaining_days = (
            #         (
            #             current_subscription.start_date
            #             + timedelta(days=current_duration_package.duration_days)
            #         )
            #         - datetime.now(timezone.utc)
            #     ).days

            #     if is_upgrading and remaining_days > 0:
            #         current_value_per_day = (
            #             current_duration_package.price
            #             * current_subscription.channel_count
            #         ) / remaining_days

            #         addable_days = (
            #             duration_package.duration_days * current_value_per_day
            #         ) / (duration_package.price * channel_count)

            total_amount = duration_package.price * channel_count

            payload = {
                "redirect_url": serializer.validated_data.get("redirect_url"),
                "website_url": serializer.validated_data.get("website_url"),
                "transaction_uuid": transaction_uuid,
                "total_amount": total_amount,
                "purchase_order_name": subscription.plan_name,
            }

            payment_method = PaymentMethod.objects.filter(id=payment_method_id).first()
            handler = payment_handler(payment_method.gateway_type)

            result = handler.initiate_payment(
                payload=payload,
            )

            if not result:
                return Response(
                    {
                        "message": "Payment initiation failed",
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            payment_idx = result.get("payment_idx", None)

            if not payment_idx:
                return Response(
                    {
                        "message": "Payment initiation failed",
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            PaymentTransaction.objects.create(
                user=request.user,
                subscription=subscription,
                payment_method=payment_method,
                total_amount=total_amount,
                transaction_uuid=transaction_uuid,
                payment_idx=payment_idx,
                duration_package=duration_package,
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
            .prefetch_related("transaction_subscription")
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

        if not result or not result.get("status"):
            return Response(
                {
                    "message": "Failed to verify payment",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                }
            )

        result_data = result.get("data")
        result_status = result_data.get("status")
        data = result_data.get("data")

        payment_transaction.status = result_status
        payment_transaction.gateway_response = data
        payment_transaction.save()

        if payment_transaction.status == "COMPLETED":
            subscription = Subscription.objects.filter(
                id=payment_transaction.subscription, is_active=True
            )

            current_subscription = UserSubscription.objects.filter(
                user=request.user, is_active=True
            ).first()

            duration_package = (
                DurationPackage.objects.select_related("subscription")
                .filter(id=payment_transaction.duration_package)
                .first()
            )

            channel_count = payment_transaction.transaction_subscription.channel_count

            if current_subscription.subscription.plan_type != "free":
                is_upgrading = (
                    current_subscription.subscription.order < subscription.order
                )
                is_downgrading = (
                    current_subscription.subscription.order > subscription.order
                )

                current_duration_package = DurationPackage.objects.filter(
                    subscription=current_subscription.subscription, is_active=True
                ).first()

                if not current_duration_package:
                    return Response(
                        {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Current duration package not found",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                remaining_days = (
                    (
                        current_subscription.start_date
                        + timedelta(days=current_duration_package.duration_days)
                    )
                    - datetime.now(timezone.utc)
                ).days

                if is_upgrading and remaining_days > 0:
                    current_value_per_day = (
                        current_duration_package.price
                        * current_subscription.channel_count
                    ) / remaining_days

                    addable_days = (
                        duration_package.duration_days * current_value_per_day
                    ) / (duration_package.price * channel_count)

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
