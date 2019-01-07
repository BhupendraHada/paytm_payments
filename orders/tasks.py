import logging
import requests
from django.conf import settings
from paytm_payment.celery_task import task
from rest_framework import status
from orders.models import OrdersTransaction, PAYTM_TRANSACTION_STATUS
from orders.paytm_checksum import generate_checksum


logger = logging.getLogger(__name__)

@task
def paytm_transaction_status_check_task(lead):
    try:
        status_check_url = 'https://securegw.paytm.in/merchant-status/getTxnStatus'
        transaction_list = OrdersTransaction.objects.filter(lead_id=lead.id)
        params = {
            "MID": settings.PAYTM_MID,
            "CUST_ID": lead.user.contact_number,
            "CHANNEL_ID": settings.PAYTM_CHANNEL_ID,
            "INDUSTRY_TYPE_ID": settings.PAYTM_INDUSTRY_TYPE_ID,
            "WEBSITE": settings.PAYTM_WEBSITE
        }
        for transaction in transaction_list:
            params["ORDER_ID"] = transaction.transaction_id
            params["TXN_AMOUNT"] = transaction.booking_amount
            # Paytm checksum generate
            checksum = generate_checksum(params)
            _request_data = {"MID": settings.PAYTM_MID, "ORDERID": transaction.transaction_id, "CHECKSUMHASH": checksum}

            # Paytm Transaction Status API call
            _response = requests.post(status_check_url, json=_request_data)

            if _response.status_code == status.HTTP_200_OK:
                _gateway_response = _response.json()
                transaction.transaction_status = PAYTM_TRANSACTION_STATUS.get(_gateway_response.get('STATUS'), 1)
                transaction.payment_gateway_response = _gateway_response
            transaction.payment_status_check = True
            transaction.save()
    except Exception as e:
        print e.__str__()
        logger.error(e.__str__())
