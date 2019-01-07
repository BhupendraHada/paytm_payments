from __future__ import unicode_literals
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from orders.constants import TransactionStatus
from django.contrib.postgres.fields import JSONField


TRANSACTION_STATUS = (
        (TransactionStatus.INPROGRESS._value_, 'Inprogress'),
        (TransactionStatus.INITIATED._value_, 'Initiated'),
        (TransactionStatus.COMPLETED._value_, 'Completed'),
        (TransactionStatus.FAILED._value_, 'Failed'),
        (TransactionStatus.CANCELLED._value_, 'Cancelled'),
        (TransactionStatus.REFUNDED._value_, 'Refunded'),

)


PAYTM_TRANSACTION_STATUS = {
    "OPEN": TransactionStatus.INITIATED,
    "PENDING": TransactionStatus.PENDING,
    "TXN_SUCCESS": TransactionStatus.COMPLETED,
    "TXN_FAILURE": TransactionStatus.FAILED,
}


class Booking(object):
    BOOKING_AMOUNT = 199

    def __init__(self):
        pass

    def get_booking_amount(self):
        return self.BOOKING_AMOUNT


class Orders(models.Model):
    class Meta:
        db_table = 'orders'

    def __str__(self):
        return self.uuid.__str__()

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AbstractUser, related_name="user_payments")


class OrdersTransaction(models.Model):
    class Meta:
        db_table = 'order_transaction'

    def __str__(self):
        return self.uuid.__str__()

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AbstractUser, related_name="user_payments")
    transaction_id = models.CharField(max_length=100, null=False)
    is_transaction_used = models.BooleanField(help_text="Whether this particular transaction is used by user?",
                                              default=False)
    transaction_status = models.IntegerField(choices=TRANSACTION_STATUS, default=TransactionStatus.INITIATED)
    booking_amount = models.FloatField(null=False, default=0.0)
    payment_gateway_response = JSONField(null=True)
    payment_status_check = models.BooleanField(default=False)
    order = models.ForeignKey(Orders)

    @staticmethod
    def latest_unused_successful_transaction(user=None):
        if user:
            # TODO: Check whether the user has crossed the limit of number of bikes for the booking amount
            # TODO: Need to check which transaction we would be consider as done
            _all_unused_successful_transactions = OrdersTransaction.objects.filter(
                transaction_status=TransactionStatus.COMPLETED._value_, user=user, is_transaction_used=False)\
                .order_by("-created")
            if _all_unused_successful_transactions.__len__():
                # Return latest unused successful transaction
                return _all_unused_successful_transactions[0]
        return None

    def update_transaction_status(self, transaction_status, request=None):
        self.transaction_status = transaction_status
        self.save()

    def update_payment_gateway_response(self, gateway_response=None, request=None):
        self.payment_gateway_response = gateway_response
        self.save()
