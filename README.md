py-pwinty: Python client for the Pwinty photo printing API
==========================================================

This library implements a Python client for the [Pwinty photo printing API](http://www.pwinty.com/Api). to make things a little more "Pythonic" all attributes are avalible in CamelCase as well as their original under_score notation.


Requirements
============

* This has only been tested on Python 2.7, it will probably work on 2.6+. It does not currently support Python 3.

* The [requests library](http://docs.python-requests.org/)


Installing
==========
It can be installed using PIP from PyPi:

    > pip install pwinty


Placing an order
================

Import pwinty and set your API Key and Merchent ID:

    import pwinty
    pwinty.apikey = "xxxxxxx"
    pwinty.merchantid = "xxxxxxx"

Create an Order:

    order = pwinty.Order.create(
        recipient_name =         	'Mr Jones',
        address_1 =              	'The Hollies',
        address_2 =              	'',
        address_town_or_city =   	'Cardiff',
        state_or_county =        	'Glamorgan',
        postal_or_zip_code =     	'CF11 1AX',
        destination_country_code =	'GB',
        country_code =           	'GB',
        qualityLevel =           	'Pro'
    )

Add photos to the order:

	photo = order.photos.create(
	    type =   	'8x12',
	    url =    	'http://www.testserver.com/aphoto.jpg',
	    md5Hash =	'79054025255fb1a26e4bc422aef54eb4',
	    copies = 	'2',
	    sizing = 	'Crop'
	)

Check the order is valid:

	order_status = order.get_submission_status()
	if not order_status.is_valid:
		print "Invalid Order"

Submit the order:

    pwinty_order.submit()


Retrieving a previous order
===========================

You can retrieve a previous order and check its status like so:

    order = pwinty.Order.get(8765)
    if order.status == 'Complete':
    	print "Order has dispatched"
