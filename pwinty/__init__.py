"""
Python client for the Pwinty photo printing API

Copyright Sam Willis <sam.willis@gmail.com> 2014
http://www.github.com/samwillis/py-pwinty

"""

import requests  # The onle none standard requirement
import json
import pprint
import hashlib


apikey = None       # Set to your Pwinty API Key
merchantid = None   # Set to your Pwinty API Merchant ID
sandbox = False     # Sets whether to use the sandbox or live API

VERSION = '0.3'

# The HTTP endpoints for the api
LIVE_API_URL = "https://api.pwinty.com/v2/"
SANDBOX_API_URL = "https://sandbox.pwinty.com/v2/"


def set_apikey(value):
    """
    This function can be used to set the API Key.
    Alternatvly you can do:
    >>> import pwinty
    >>> pwinty.apikey = "xxxxxxx"
    """
    apikey = value

def set_merchantid(value):
    """
    This function can be used to set the Merchant ID.
    Alternatvly you can do:
    >>> import pwinty
    >>> pwinty.merchantid = "xxxxxxx"
    """
    merchantid = value

def underscore_to_camelcase(value):
    """
    Converts underscore notation (something_named_this) to camelcase notation (somethingNamedThis)

    >>> underscore_to_camelcase('country_code')
    'countryCode'
    >>> underscore_to_camelcase('country')
    'country'
    >>> underscore_to_camelcase('price_GBP')
    'priceGBP'
    >>> underscore_to_camelcase('recommended_horizontal_resolution')
    'recommendedHorizontalResolution'
    >>> underscore_to_camelcase('postal_or_zip_code')
    'postalOrZipCode'
    >>> underscore_to_camelcase('test_ABC_test')
    'testABCTest'
    """
    words = value.split('_')
    return '%s%s' % (words[0], ''.join(x if x.isupper() else x.capitalize() for x in words[1:]))

def underscore_to_camelcase_dict(d):
    "Converts a dicts keys to camelcase"
    return {underscore_to_camelcase(key):value for key, value in d.items()}

def camelcase_to_underscore(value):
    """
    Converts camelcase notation (somethingNamedThis) to underscore notation (something_named_this)

    >>> camelcase_to_underscore('countryCode')
    'country_code'
    >>> camelcase_to_underscore('country')
    'country'
    >>> camelcase_to_underscore('priceGBP')
    'price_GBP'
    >>> camelcase_to_underscore('recommendedHorizontalResolution')
    'recommended_horizontal_resolution'
    >>> camelcase_to_underscore('postalOrZipCode')
    'postal_or_zip_code'
    >>> camelcase_to_underscore('testABCTest')
    'test_ABC_test'
    """
    length = len(value)
    out = ''
    for i in xrange(length):
        char = value[i]
        last_char = value[i-1]
        next_char = None
        if i != length-1:
            next_char = value[i+1]
        if i == 0 or char.islower():
            out += char
        elif last_char.islower():
            if next_char and next_char.isupper():
                out += '_%s' % char
            else:
                out += '_%s' % char.lower()
        else:
            if next_char and next_char.islower():
                out += '_%s' % char.lower()
            else:
                out += char
    return out

def _request(end_point, method, params=None, data=None, files=None):
    headers = {
        'X-Pwinty-MerchantId': merchantid,
        'X-Pwinty-REST-API-Key': apikey
    }
    if not data and not files:
        headers['Content-Length'] = '0'

    if sandbox:
        url = SANDBOX_API_URL
    else:
        url = LIVE_API_URL

    if params:
        params = underscore_to_camelcase_dict(params)
    if data:
        data = underscore_to_camelcase_dict(data)
    if files:
        files = underscore_to_camelcase_dict(files)

    print method, url + end_point
    r = requests.request(method, url + end_point, headers=headers, params=params, data=data, files=files)

    if r.status_code in (200, 201):
        if r.text:
            return json.loads(r.text)
        else:
            return r.content
    else:
        if r.text:
            json_obj = json.loads(r.text)
            if 'errorMessage' in json_obj:
                message = json_obj['errorMessage']
            else:
                message = json_obj['Message']
            response = r.text
        else:
            message = r.content
            response = r.content
        if r.status_code == 400:
            raise PwintyBadInputError(message, response)
        elif r.status_code == 403:
            raise PwintyForbiddenError(message, response)
        elif r.status_code == 404:
            raise PwintyMissingError(message, response)
        elif r.status_code == 500:
            raise PwintyServerError(message, response)
        else:
            raise PwintyError(message, response, r.status_code)


class Resource(object):
    def __init__(self, json):
        self._json = json

    _json = {}
    _id_field_name = None
    _editable_fields = ()

    def keys(self):
        hide_keys = ('photos',)
        return [camelcase_to_underscore(key) for key in self._json.keys() if key not in hide_keys] 

    def get_dict(self):
        return {key: self.__getattr__(key) for key in self.keys()}

    def get_json(self):
        return self._json

    def items(self):
        return self.get_dict().items()

    def values(self):
        return seld.get_dict().values()

    def __getattr__(self, name):
        name = underscore_to_camelcase(name)
        if name in self._json:
            value = self._json[name]
            if type(value) == dict:
                value = Resource(value)
            elif type(value) == list:
                value = [Resource(v) if type(v)==dict else v for v in value]
            return value
        else:
            raise ValueError()

    def __setattr__(self, name, value):
        nameC = underscore_to_camelcase(name)
        if nameC in self._json:
            if nameC in self._editable_fields:
                self._json[nameC] = value
            else:
                raise ValueError('Value readonly: %s' % name)
        else:
            super(Resource, self).__setattr__(name, value)

    def __cmp__(self, other):
        if self._id_field_name:
            return self.__getattr__(self._id_field_name) - other.__getattr__(self._id_field_name)
        else:
            super(Resource, self).__cmp__(other)

    def __repr__(self):
        id_string = ''
        if self._id_field_name:
            id_string = ' %s=%s' % (self._id_field_name, self.__getattr__(self._id_field_name))
        return '<%s%s at %s>' % (type(self).__name__, id_string, hex(id(self)))


class Catalogue(Resource):
    @classmethod
    def get(cls, country_code, quality_level='Standard'):
        res = _request('Catalogue/%s/%s' % (country_code, quality_level), 'GET')
        return cls(res)


class Photo(Resource):
    _id_field_name = 'id'

    @classmethod
    def create(cls, order_id, **kwargs):
        files = None
        file_opend = False
        md5 = None
        file_obj = None

        try:
            if "file_path" in kwargs:
                # We have a file path so open file, make md5 hash and add to files to upload
                file_obj = open(kwargs['file_path'], 'rb')
                file_opend = True
                md5 = hashlib.md5(file_obj.read()).hexdigest()
                files = {'file': f}
                del kwargs['file_path']

            elif "file" in kwargs:
                # We have an open file so make an md5 hash and add to files to upload
                file_obj = kwargs['file']
                md5 = hashlib.md5(file_obj.read()).hexdigest()
                files = {'file': f}
                del kwargs['file']

            elif "url" not in kwargs:
                raise PwintyException("file_path, file OR url required")

            if md5:
                kwargs['md5Hash'] = md5

            res = _request('Orders/%s/Photos' % order_id, 'POST', data=kwargs, files=files)

        finally:
            if file_opend:
                file_obj.close()

        return cls(res)
    
    @classmethod
    def get(cls, order_id, id):
        res = _request('Orders/%s/Photos/%s' % (order_id, id), 'GET')
        return cls(res)

    def delete(self):
        res = _request('Orders/%s/Photos/%s' % (self.order_id, self.id), 'DELETE')
        return cls(res)


class OrderPhotos(object):
    def __init__(self, order_id):
        self._order_id = order_id

    def create(self, **kwargs):
        return Photo.create(self._order_id, **kwargs)

    def get(self, id):
        return Photo.get(self._order_id, id)

    def all(self):
        res = _request('Orders/%s/Photos' % self._order_id, 'GET')
        return [Photo(o) for o in res]


class Order(Resource):
    _id_field_name = 'id'
    _editable_fields = ('recipientName', 'address1', 'address2', 'addressTownOrCity', 'stateOrCounty', 'postalOrZipCode')

    @classmethod
    def create(cls, **kwargs):
        res = _request('Orders', 'POST', data=kwargs)
        return cls(res)
    
    @classmethod
    def get(cls, id):
        res = _request('Orders/%s' % id, 'GET')
        return cls(res)
    
    @classmethod
    def all(cls):
        res = _request('Orders', 'GET')
        return [cls(o) for o in res]

    def save(self):
        options = {}
        for name in self._editable_fields:
            if name in self._json:
                options[name] = self._json[name]
        res = _request('Orders/%s' % self.id, 'PUT', options)
        self._json = res  # Update this object with any changes

    def cancel(self):
        res = _request('Orders/%s/Status' % self.id, 'POST', data={'status': 'Cancelled'})
        self.refresh()

    def submit(self):
        res = _request('Orders/%s/Status' % self.id, 'POST', data={'status': 'Submitted'})
        self.refresh()

    def await_payment(self):
        res = _request('Orders/%s/Status' % self.id, 'POST', data={'status': 'AwaitingPayment'})
        self.refresh()

    def get_submission_status(self):
        res = _request('Orders/%s/SubmissionStatus' % self.id, 'GET')
        return Resource(res)

    def refresh(self):
        res = _request('Orders/%s' % self.id, 'GET')
        self._json = res  # Update this object with any changes

    @property
    def photos(self):
        return OrderPhotos(self.id)


class Country(Resource):
    _id_field_name = 'countryCode'

    @classmethod
    def all(cls):
        res = _request('Country', 'GET')
        return [cls(o) for o in res]


class PwintyException(Exception):
    pass


class PwintyError(PwintyException):
    def __init__(self, message, response, status_code):
        self.message = message
        self.response = response
        self.status_code = status_code

    def __str__(self):
        return '%s (%s)' % (self.message, self.status_code)


class PwintyBadInputError(PwintyError):
    def __init__(self, message, response):
        super(PwintyBadInputError, self).__init__(message, response, 400)


class PwintyForbiddenError(PwintyError):
    def __init__(self, message, response):
        super(PwintyForbiddenError, self).__init__(message, response, 403)


class PwintyMissingError(PwintyError):
    def __init__(self, message, response):
        super(PwintyMissingError, self).__init__(message, response, 404)


class PwintyServerError(PwintyError):
    def __init__(self, message, response):
        super(PwintyServerError, self).__init__(message, response, 500)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

