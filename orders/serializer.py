from django.conf import settings
from django.db.transaction import atomic
from rest_framework import serializers
from orders.models import OrdersTransaction

class OrderTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersTransaction
        fields = ("user", "lead", "transaction_id", "booking_amount", "payment_gateway_response", "payment_status_check")
        extra_kwargs = {
            'transaction_id': {
              "required": False
            },
            'transaction_status': {
                'required': False,
                'read_only': True
            },
            'booking_amount': {
                'required': False
            },
            'payment_status_check': {
                'required': False
            },
            'payment_gateway_response': {
                'required': False
            }
        }

    @atomic
    def create(self, validated_data):
        order = OrdersTransaction(**validated_data)
        order.save()
        return order
