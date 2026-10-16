from rest_framework import serializers
from .models import PaymentTransaction


class PaymentInitializeSerializer(serializers.Serializer):
    PACKAGE_CHOICES = ['monthly', 'yearly']

    channel_count = serializers.IntegerField(write_only=True)
    package_type = serializers.ChoiceField(choices=PACKAGE_CHOICES)
    payment_method_id = serializers.IntegerField(write_only=True)
    subscription_id = serializers.IntegerField(write_only=True)
    redirect_url = serializers.CharField(write_only=True)
    website_url = serializers.CharField(write_only=True)
    transaction_uuid = serializers.CharField()

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model=PaymentTransaction
        fields="__all__"
    
