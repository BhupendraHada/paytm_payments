import random
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView
from django.contrib.auth.models import AbstractUser
from paymentservclient.base import PaymentServClient
from orders.serializer import OrderTransactionSerializer
from orders.models import Orders, OrdersTransaction, Booking
from orders.tasks import paytm_transaction_status_check_task

class BookingCheckoutAPIView(ListCreateAPIView):
    lead_id = None
    lead = None
    user_id = None
    user = None
    booking_amount = None
    transaction_id = None
    response = None
    paymentserv_response = None
    all_successful_transactions = None
    paymentserv_client = PaymentServClient

    """
    Booking checkout View
    """
    serializer_class = OrderTransactionSerializer
    queryset = OrdersTransaction.objects.all().order_by("id")

    def _initialize_and_validate(self, request):
        self.order_id = request.get('lead_id')
        # TODO: Handle DoesNotExistException
        self.order = Orders.objects.get(id=self.order_id)
        self.user_id = request.get('user_id')
        self.user = AbstractUser.objects.get(id=self.user_id)
        self.booking_amount = Booking().get_booking_amount()
        self.latest_unused_successful_transaction = OrdersTransaction().latest_unused_successful_transaction(
            user=self.user)

    def _check_if_already_paid(self):
        return self.order.user_successful_transactions(user=self.user)

    @staticmethod
    def _set_user_id(request):
        # Set User ID in request data
        request.data["user"] = self.user_id

    @staticmethod
    def _set_transaction_id(request, transaction_id=None):
        if transaction_id:
            request.data["transaction_id"] = transaction_id
        else:
            request.data["transaction_id"] = "companyname-" + "%0.12d" % random.randint(0, 999999999999)

    @staticmethod
    def _set_booking_amount(request, booking_amount=0):
        request.data["booking_amount"] = booking_amount

    def _pre_sending_response_activities(self):
        #schedule task to be run after 10 mins to check payment status

        paytm_transaction_status_check_task.apply_async(
            args=[self.order],
            countdown=10,
            queue='celery_task',
            routing_key='celery_task',
        )


    def _get_payment_response(self, request):
        # TODO: Move paymentserv to Django and accordingly change the logic
        _payload = {
            "meta": {
                "website": "CompanyNameweb",
                "channel_id": "WEB",
                "gateway_name": "paytm",
                "gateway_value": 1
            },
            "payload": {
                "city": 1,
                "product_id": 1,
                "order_id": self.order_id,
                "source": "web",
                "user": {
                    "contact_number": self.user.contact_number.__str__(),
                    "email": ""
                },
                "txn_amount": self.booking_amount
            }
        }

        _client = self.paymentserv_client()
        try:
            _response = _client.generate_transaction_payload(data=json.dumps(_payload))
            if _response.status_code == status.HTTP_200_OK:
                request.data["payment_status_check"] = True
                return _response.json()
            else:
                raise Exception

        except Exception as e:
            logger.error(e.__str__())
            return e.__str__()

    def post(self, request, *args, **kwargs):
        _transaction_id = None
        try:
            self._initialize_and_validate(request=request)
            self._set_user_id(request)
            if self.latest_unused_successful_transaction:
                response = UserHasAlreadyPaidForB2CBooking().response()
                _transaction_id = self.latest_unused_successful_transaction.transaction_id
            else:
                response = self._get_payment_response(request)
                if response.get("meta") and response.get("meta").get("transaction_id"):
                    _transaction_id = response.get("meta").get("transaction_id")

            if _transaction_id:
                self._set_transaction_id(request=request, transaction_id=_transaction_id)
                self._set_booking_amount(request, self.booking_amount)

            _serializer = self.serializer_class(data=request.data)
            if _serializer.is_valid():
                _serializer.save()

            self._pre_sending_response_activities()
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(e.__str__())
            return Response(e.__str__(), status=status.HTTP_400_BAD_REQUEST)


class BookingPaymentGatewayCallbackAPIView(APIView):
    """
    Booking Callback API Handler
    -- As of now only for PayTM.
    """
    lead = None
    user_id = None
    user = None
    transaction_id = None
    request = None
    response = dict()
    successful_redirect = settings.PAYMENTSUCCESSFUL_URL
    unsuccessful_redirect = settings.PAYMENTFAILURE_URL
    callback_url_query = dict()
    base64encoded_callback_url_query = None
    callback_redirect_url = ""
    gateway_request_payload = None
    paymentserv_request_payload = dict()
    paytm = 1
    paymentserv_client = PaymentServClient

    serializer_class = OrderTransactionSerializer
    queryset = OrdersTransaction.objects.all().order_by("id")

    def _initialize_and_validate(self, request):
        self.request = request
        self.gateway_request_payload = dict(zip(request.POST.keys(), request.POST.values()))
        self.paymentserv_request_payload.update(
            {"meta": {"gateway_name": "paytm", "gateway_value": 1}, "payload": self.gateway_request_payload})

    def _verify_payment(self):
        _client = self.paymentserv_client()
        try:
            _response = _client.verify_transaction(data=json.dumps(self.paymentserv_request_payload))
            if _response.status_code == status.HTTP_200_OK:
                return _response.json()
            else:
                raise Exception

        except Exception as e:
            logger.error(e.__str__())
            return e.__str__()

    def _set_transaction_id(self, transaction_id=None):
        self.transaction_id = transaction_id

    def _set_order(self):
        try:
            self.order = self.queryset.get(transaction_id=self.transaction_id)
        except ObjectDoesNotExist:
            raise BookingTransactionDoesNotExistException(request=self.request, transaction_id=self.transaction_id)
        except MultipleObjectsReturned:
            raise MultipleBookingTransactionsForGivenTransactionIdException(request=self.request,
                                                                            transaction_id=self.transaction_id)

        except BookingTransactionDoesNotExistException as e:
            logger.error(e.get_exception_log_object(label=settings.CREDR_CORE_PAYTM_CALLBACK_API_ERROR))

        except MultipleBookingTransactionsForGivenTransactionIdException as e:
            logger.error(e.get_exception_log_object(label=settings.CREDR_CORE_PAYTM_CALLBACK_API_ERROR))

    def _set_callback_url_query(self):
        self.callback_url_query.update({"txm_amount": self.order.booking_amount})
        self.callback_url_query.update({"lead_id": self.order.id})
        self.base64encoded_callback_url_query = base64.b64encode(JSONRenderer().render(self.callback_url_query))

    def _update_payment_gateway_response(self):
        self.order.update_payment_gateway_response(self.gateway_request_payload, request=self.request)

    def post(self, request, *args, **kwargs):
        try:
            logger.info("1) inside callback BookingPaymentGatewayCallbackAPIView function: %s" % (str(request, )))
            logger.info("2) kwargs callback api %s" % (str(kwargs),))
            self._initialize_and_validate(request=request)
            _paymentserv_response = self._verify_payment()
            if _paymentserv_response.get("payload") and _paymentserv_response.get("payload").get("transaction_id"):
                _transaction_id = _paymentserv_response.get("payload").get("transaction_id")
                self._set_transaction_id(_transaction_id)
                self._set_order()
                self._update_payment_gateway_response()
            self._set_callback_url_query()

            if _paymentserv_response.get("payload") and _paymentserv_response.get("payload").get(
                    "is_transaction_valid"):
                self.order.update_transaction_status(transaction_status=TransactionStatus.COMPLETED._value_,
                                                    request=self.request)
                self.callback_redirect_url = self.successful_redirect + self.base64encoded_callback_url_query
            else:
                self.order.update_transaction_status(transaction_status=TransactionStatus.FAILED._value_,
                                                    request=self.request)
                self.callback_redirect_url = self.unsuccessful_redirect + self.base64encoded_callback_url_query
                # TODO: Schedule a task to send an SMS to the customer to pay again or handle it on Tesla
            return HttpResponseRedirect(redirect_to=self.callback_redirect_url)

        except Exception as e:
            _exception = CredrBaseException(request=request, custom_message=e.__str__())
            logger.error(_exception.get_exception_log_object(label=settings.CREDR_CORE_PAYTM_CALLBACK_API_ERROR))
            if self.order:
                self.order.update_transaction_status(transaction_status=TransactionStatus.FAILED._value_,
                                                    request=self.request)
                self.callback_redirect_url = self.unsuccessful_redirect + self.base64encoded_callback_url_query
            return Response(json.loads(_exception.response()), status=status.HTTP_400_BAD_REQUEST)

        except PaymentservServerError as e:
            if self.order:
                self.order.update_transaction_status(transaction_status=TransactionStatus.FAILED._value_,
                                                    request=self.request)
                self.callback_redirect_url = self.unsuccessful_redirect + self.base64encoded_callback_url_query
            logger.error(e.get_exception_log_object(label=settings.CREDR_CORE_PAYTM_CALLBACK_PAYMENT_API_ERROR))
            return Response(e.response(), status=status.HTTP_400_BAD_REQUEST)
