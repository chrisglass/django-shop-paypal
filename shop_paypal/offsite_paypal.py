#-*- coding: utf-8 -*-
from decimal import Decimal

from django.conf import settings
from django.conf.urls.defaults import patterns, url, include
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.signals import payment_was_successful as success_signal


class OffsitePaypalBackend(object):
    '''
    Glue code to let django-SHOP talk to django-paypal's.

    The django-paypal package already defines an IPN view, that logs everything
    to the database (desirable), and fires up a signal.
    It is therefore more convenient to listen to the signal instead of
    rewriting the ipn view (and necessary tests)
    '''

    backend_name = "Paypal"
    url_namespace = "paypal"

    #==========================================================================
    # Defined by the backends API
    #==========================================================================

    def __init__(self, shop):
        self.shop = shop

        # Hook the payment was successful listener on the appropriate signal
        # sent by django-paypal (success_signal)
        unique_key = 'django-shop-paypal_offsite_payment-successful'
        success_signal.connect(self.payment_was_successful, weak=False,
                               dispatch_uid=unique_key)

        assert settings.PAYPAL_RECEIVER_EMAIL, "You need to define " \
                                               "PAYPAL_RECEIVER_EMAIL in " \
                                               "settings with the " \
                                               "recipient's email addresss"

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.view_that_asks_for_money, name='paypal'),
            url(r'^success/$', self.paypal_successful_return_view,
                name='paypal_success'),
            url(r'^somethinghardtoguess/instantpaymentnotification/$',
                include('paypal.standard.ipn.urls')),
        )
        return urlpatterns

    def get_form(self, request):
        '''
        Configures a paypal form and returns. Allows this code to be reused
        in other views.
        '''
        order = self.shop.get_order(request)
        url_scheme = 'https' if request.is_secure() else 'http'
        # get_current_site requires Django 1.3 - backward compatibility?
        url_domain = get_current_site(request).domain

        try:
            business = settings.PAYPAL_BUSINESS
        except AttributeError:
            business = settings.PAYPAL_RECEIVER_EMAIL

        try:
            currency_code = self.shop.get_order_currency(order)
        except AttributeError:
            currency_code = settings.PAYPAL_CURRENCY_CODE

        paypal_dict = {
            "business": business,
            "currency_code": currency_code,
            "amount": self.shop.get_order_total(order),
            "item_name": self.shop.get_order_short_name(order),
            "invoice": self.shop.get_order_unique_id(order),
            # NOTE: defined by django-paypal
            "notify_url": '%s://%s%s' % (url_scheme, url_domain,
                                         reverse('paypal-ipn')),
            # NOTE: That's this classe's view
            "return_url": '%s://%s%s' % (url_scheme, url_domain,
                                         reverse('paypal_success')),
            # NOTE: A generic one
            "cancel_return": '%s://%s%s' % (url_scheme, url_domain,
                                            self.shop.get_cancel_url()),
        }
        if hasattr(settings, 'PAYPAL_LC'):
            paypal_dict['lc'] = settings.PAYPAL_LC

        # Create the instance.
        form = PayPalPaymentsForm(initial=paypal_dict)
        return form

    #==========================================================================
    # Views
    #==========================================================================

    def view_that_asks_for_money(self, request):
        '''
        We need this to be a method and not a function, since we need to have
        a reference to the shop interface
        '''
        form = self.get_form(request)
        context = {"form": form}
        rc = RequestContext(request, context)
        return render_to_response("shop_paypal/payment.html", rc)

    @csrf_exempt
    def paypal_successful_return_view(self, request):
        if getattr(settings, "PAYPAL_SUCCESS_REDIRECT_TO_THANKYOU", False):
            return HttpResponseRedirect(self.shop.get_finished_url())

        rc = RequestContext(request, {})
        return render_to_response("shop_paypal/success.html", rc)

    #==========================================================================
    # Signal listeners
    #==========================================================================

    def payment_was_successful(self, sender, **kwargs):
        '''
        This listens to the signal emitted by django-paypal's IPN view and in
        turn asks the shop system to record a successful payment.
        '''
        ipn_obj = sender
        order_id = ipn_obj.invoice  # Invoice ID we passed to Paypal
        amount = Decimal(ipn_obj.mc_gross)
        transaction_id = ipn_obj.txn_id
        order = self.shop.get_order_for_id(order_id)
        # The actual request to the shop system
        # TODO: Should check ipn_obj.flag
        self.shop.confirm_payment(order, amount, transaction_id,
                                  self.backend_name)
