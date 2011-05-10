#-*- coding: utf-8 -*-
from decimal import Decimal

from django.conf import settings
from django.conf.urls.defaults import patterns, url, include
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.signals import payment_was_successful as success_signal


class OffsitePaypalBackend(object):
    '''
    Glue code to let django-SHOP talk to django-paypal's.
    
    The django-paypal package already defines an IPN view, that logs everything
    to the database (desirable), and fires up a signal.
    It is therefore more convenient to listen to the signal instead of rewriting
    the ipn view (and necessary tests)
    '''
    
    backend_name = "Paypal"
    url_namespace = "paypal"
    
    #===========================================================================
    # Defined by the backends API
    #===========================================================================
    
    def __init__(self, shop):
        self.shop = shop
        # Hook the payment was successful listener on the appropriate signal sent
        # by django-paypal (success_signal)
        success_signal.connect(self.payment_was_successful, weak=False)
        assert settings.PAYPAL_RECEIVER_EMAIL, "You need to define a PAYPAL_RECEIVER_EMAIL in settings with the money recipient's email addresss"
        
    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.view_that_asks_for_money, name='paypal' ),
            url(r'^success$', self.paypal_successful_return_view, name='paypal_success' ),
            url(r'^/somethinghardtoguess/instantpaymentnotification/$', include('paypal.standard.ipn.urls')),
        )
        return urlpatterns
    
    #===========================================================================
    # Views
    #===========================================================================
    
    def view_that_asks_for_money(self, request):
        '''
        We need this to be a method and not a function, since we need to have
        a reference to the shop interface
        '''
        order = self.shop.get_order(request)
        url_scheme = 'https' if request.is_secure() else 'http'
        # get_current_site requires Django 1.3 - backward compatibility?
        url_domain = get_current_site(request).domain
        paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": self.shop.get_order_total(order),
        "item_name": self.shop.get_order_short_name(order),
        "invoice": self.shop.get_order_unique_id(order),
        "notify_url": '%s://%s%s' % (url_scheme, 
            url_domain, reverse('paypal-ipn')), # defined by django-paypal
        "return_url": '%s://%s%s' % (url_scheme,
            url_domain, reverse('paypal_success')), # That's this classe's view
        "cancel_return": '%s://%s%s' % (url_scheme,
            url_domain, self.shop.get_cancel_url()), # A generic one
        }

        # Create the instance.
        form = PayPalPaymentsForm(initial=paypal_dict)
        context = {"form": form}
        return render_to_response("shop_paypal/payment.html", context)
    
    def paypal_successful_return_view(self, request):
        return render_to_response("shop_paypal/success.html", {})
    
    #===========================================================================
    # Signal listeners
    #===========================================================================
    
    def payment_was_successful(self, sender, **kwargs):
        '''
        This listens to the signal emitted by django-paypal's IPN view and in turn
        asks the shop system to record a successful payment.
        '''
        ipn_obj = sender
        order_id = ipn_obj.invoice # That's the "invoice ID we passed to paypal
        amount = Decimal(ipn_obj.auth_amount)
        transaction_id = ipn_obj.txn_id
        # The actual request to the shop system
        self.shop.confirm_payment(self.shop.get_order_for_id(order_id), amount, transaction_id, self.backend_name)
        
        
    
