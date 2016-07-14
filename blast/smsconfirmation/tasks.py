import base64
import datetime
import hashlib
import hmac
import json
import requests

import blast.celery

from django.conf import settings

from celery import shared_task

from smsconfirmation.models import PhoneConfirmation


def sinch_request(resource, data, method):
    headers = {
        'X-Timestamp': datetime.datetime.utcnow().isoformat(),
        'Content-Type': 'application/json',
    }

    URL = 'https://api.sinch.com{}'.format(resource)

    scheme = 'Application'

    canonicalized_headers = '{}:{}'.format('x-timestamp', headers['X-Timestamp'])
    canonicalized_resource = resource

    data_str = json.dumps(data)
    content_md5 = hashlib.md5(data_str.encode('utf-8')).digest()
    content_md5 = base64.b64encode(content_md5)
    # assert content_md5 != 'jANzQ+rgAHyf1MWQFSwvYw==', 'Wrong md5'

    string_to_sign = '{}\n{}\n{}\n{}\n{}'.format(method,
                                                 content_md5.decode('utf-8'),
                                                 headers['Content-Type'],
                                                 canonicalized_headers,
                                                 canonicalized_resource)

    secret = base64.b64decode(settings.SINCH['APP_SECRET'])
    signature = hmac.new(secret,
                         string_to_sign.encode('utf-8'),
                         hashlib.sha256).digest()
    signature = base64.b64encode(signature)

    # assert signature != 'qDXMwzfaxCRS849c/2R0hg0nphgdHciTo7OdM6MsdnM=', "Wrong signature"

    authorization = '{} {}:{}'.format(scheme, settings.SINCH['APP_KEY'], signature.decode('utf-8'))
    headers['Authorization'] = authorization

    if method == 'POST':
        return requests.post(URL, json=data, headers=headers)
    elif method == 'PUT':
        return requests.put(URL, data=data_str, headers=headers)

    # req = request.Request(URL, data=data_str.encode('utf-8'))
    # for key, value in headers.items():
    #     req.add_header(key, value)
    # req.get_method = lambda: method

    # response = request.urlopen(req)
    # response = response.read()
    # return response


@shared_task(bind=False)
def send_code_confirmation_request(code, phone):
    print('confirm code {} {}'.format(code, phone))

    response = sinch_request('/verification/v1/verifications/number/{}'.format(phone), data={
        "sms": {"code": str(code)},
        "method": "sms",
    }, method='PUT')

    data = response.json()

    print(data, code, phone)

    if data.get('status') == 'SUCCESSFUL':
        confirm = PhoneConfirmation.objects.get_actual(phone=phone)
        confirm.is_confirmed = True
        confirm.save()

    print('send_code_confirmation_request', code, phone, response.content)


@shared_task(bind=False)
def send_verification_request(phone):
    print('verifying phone {}'.format(phone))

    response = sinch_request('/verification/v1/verifications', data={
        "identity": {"type": "number", "endpoint": str(phone)},
        "method": "sms",
    }, method='POST')

    print('send_verification_request', phone, response.content)
