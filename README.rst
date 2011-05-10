======================
django-shop-paypal
======================

This applicaiton is a paypal backend for django-SHOP, or any other shop system
implementing its shop interface.
It uses django-paypal as a way to actually communicate with paypal.

Usage
======

Add django-paypal and this project to your INSTALLED_APPS:::

  INSTALLED_APPS = (
  ...
  'paypal.standard.ipn',
  'shop_paypal',
  ...
  )

Add 'shop_paypal.offsite_paypal.OffsitePaypalBackend' to django-SHOP's SHOP_PAYMENT_BACKENDS
setting.

Set `PAYPAL_RECEIVER_EMAIL` in settings.py.

Todo
=====

Plenty of stuff is left to do! If you feel like giving a hand, please pick a task
in the follwing list:

* Implement more functionalities from django-paypal in different backends 
  (one for direct payments, one for professional accounts...)
* Port the shop API to other shop systems, so they can also easily use this 
  project as a backend. Examples include but are not limited to: plata, satchmo, 
  lfs
  
Contributing
=============

Feel free to post any comment or suggestion for this project on the django-shop 
mailing list or on #djanho-shop on freenode :)
