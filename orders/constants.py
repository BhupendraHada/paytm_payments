from enum import IntEnum


class TransactionStatus(IntEnum):
    INPROGRESS = 0
    INITIATED = 1
    COMPLETED = 2
    FAILED = 3
    REJECTED = 4
    CANCELLED = 5


PAYTM_TRANSACTION_STATUS = {
    "OPEN": TransactionStatus.INITIATED,
    "PENDING": TransactionStatus.PENDING,
    "TXN_SUCCESS": TransactionStatus.COMPLETED,
    "TXN_FAILURE": TransactionStatus.FAILED,
}