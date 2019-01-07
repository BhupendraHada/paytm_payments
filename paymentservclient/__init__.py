__author__ = 'vivekdogra'

import os
from django.conf import settings

from .base import PaymentServClient

assert settings.PAYMENTSERV.has_key("HOST"), "Please provide paymentserv hostname"
assert settings.PAYMENTSERV.has_key("PORT"), "Please provide paymentserv port"
assert settings.PAYMENTSERV_BASE, "Please provide paymentserv base"

env = os.environ.get('APP_ENV')
if env and env != "development":
    try:
        paymentservclient = PaymentServClient()
        assert (paymentservclient.ping() == "pong")
    except Exception as e:
        print "Payment Service is not up!"
        exit(0)
