__author__ = 'bhupendra'


TRANSACTION_DETAILS_API = "/api/v1/transaction/orders/{0}"
REFUND_API = "/api/v1/payments/transaction/{transaction_id}/refund"
CHECK_REFUND_STATUS_API = "/api/v1/payments/transaction/{transaction_id}/refund/status"
REFUND_HISTORY = "/api/v1/payments/refunds"
REFUND_REQUEST_STATUS ='/api/v1/payments/transaction/{transaction_id}/refund/status'
PING = "/ping/"
REQUEST_FOR_REFUND = "/api/v1/payments/refund/request"
CHECK_TRANSACTION_STATUS_API = '/api/v1/transaction/orders/{transaction_id}/status'
