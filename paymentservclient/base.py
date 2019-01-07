__author__ = 'bhupendra'

import logging
import requests
from django.conf import settings

from . import apis

logger = logging.getLogger(__name__)


class PaymentServClient(object):
    def __init__(self):
        self.headers = {'Content-Type': 'application/JSON'}
        self.order_transaction_api = apis.ORDER_TRANSACTION_API

    def ping(self):
        api = settings.PAYMENTSERV_BASE + apis.PING
        response = requests.get(url=api)
        return response.content

    # TODO: Get order according to the user_id (received from caller)
    def get_transaction_details(self, user_id, transaction_id):
        api = settings.PAYMENTSERV_BASE + apis.TRANSACTION_DETAILS_API.format(transaction_id)
        logger.info("Fetch all transaction details: ")
        logger.info(api)
        response = requests.get(url=api, headers=self.headers)
        logger.info("Response from paymentserv: ")
        logger.info(response.content)
        return response

    def initiate_transaction_refund(self, transaction_id):
        api = settings.PAYMENTSERV_BASE + apis.REFUND_API.format(transaction_id=transaction_id)
        response = requests.post(url=api)
        return response

    def get_refund_status(self, transaction_id):
        api = settings.PAYMENTSERV_BASE + apis.CHECK_REFUND_STATUS_API.format(transaction_id=transaction_id)
        response = requests.get(url=api)
        return response

    def get_refund_history(self):
        api = settings.PAYMENTSERV_BASE + apis.REFUND_HISTORY
        response = requests.get(url=api)
        return response

    def request_for_refund(self, data):
        api = settings.PAYMENTSERV_BASE + apis.REQUEST_FOR_REFUND
        response = requests.post(url=api, data=data, headers=self.headers)
        return response

    def get_transaction_status(self, user_id, transaction_id):
        api = settings.PAYMENTSERV_BASE + apis.CHECK_TRANSACTION_STATUS_API.format(transaction_id=transaction_id)
        logger.info("Fetch transaction status from gateway: ")
        logger.info(api)
        response = requests.get(url=api, headers=self.headers)
        logger.info("Response from paymentserv: ")
        logger.info(response.content)
        return response
