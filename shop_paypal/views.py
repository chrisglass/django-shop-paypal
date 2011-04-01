#-*- coding: utf-8 -*-




def view_that_asks_for_money(request):
    ''' This is lifted straight from django-paypal's readme file'''
     # What you want the button to do.
    paypal_dict = {
        "business": "yourpaypalemail@example.com",
        "amount": "10000000.00",
        "item_name": "name of the item",
        "invoice": "unique-invoice-id",
        "notify_url": "http://www.example.com/your-ipn-location/",
        "return_url": "http://www.example.com/your-return-location/",
        "cancel_return": "http://www.example.com/your-cancel-location/",

    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render_to_response("payment.html", context)