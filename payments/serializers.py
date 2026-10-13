from rest_framework import serializers


class PaymentInitializeSerializer(serializers.Serializer):
    payment_method_id = serializers.IntegerField(write_only=True)
    subscription_id = serializers.IntegerField(write_only=True)
    redirect_url = serializers.CharField(write_only=True)
    website_url = serializers.CharField(write_only=True)
    transaction_uuid = serializers.CharField()
    
