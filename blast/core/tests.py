import json
import uuid

from io import BytesIO

import redis
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.core.urlresolvers import reverse_lazy

from countries.models import Country
from users.models import User


def create_file(name, content_file=True):
    image = Image.new('RGBA', size=(50, 50))
    file = BytesIO(image.tostring())
    file.name = name
    file.seek(0)

    if content_file:
        return ContentFile(file.read(), name=name)
    else:
        return SimpleUploadedFile(name, file.read(), content_type='image/png')


class BaseTestCaseUnauth(TestCase):
    phone = '8913123123'
    password = '111111'
    username = 'username'

    def generate_user(self, username=None):
        if not username:
            username = str(uuid.uuid4())

        return User.objects.create_user(username=username, password=self.password,
                                        country=self.country, phone=uuid.uuid4())

    def login(self, username,):
        data = {
            'username': username,
            'password': self.password
        }

        response = self.client.post(reverse_lazy('get-auth-token'), data)
        self.auth_token = response.data.get('token')
        self.headers = {
            'HTTP_AUTHORIZATION': 'Token {0}'.format(self.auth_token)
        }
        self.client.defaults.update(self.headers)

    def setUp(self):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.r.flushdb()

        data = {
            'phone': self.phone,
            'username': self.username,
            'password': self.password,
        }

        self.country = Country.objects.create(name='Russia', code='+7')

        self.anonymous = User.objects.create(username='Anonymous', password=uuid.uuid4(),
                                             phone='+', country=self.country)

        self.user = User.objects.create_user(**data)

        data = {
            'username': self.username,
            'password': self.password
        }

        response = self.client.post(reverse_lazy('get-auth-token'), data)
        self.auth_token = response.data.get('token')

    def put_json(self, url, data=''):
        if type(data) is dict:
            data = json.dumps(data)

        return self.client.put(url, data=data, content_type='application/json')

    def patch_json(self, url, data=''):
        return self.client.patch(url, json.dumps(data),
                                 content_type='application/json')


class BaseTestCase(BaseTestCaseUnauth):
    def setUp(self):
        super().setUp()

        self.headers = {
            'HTTP_AUTHORIZATION': 'Token {0}'.format(self.auth_token)
        }
        self.client.defaults.update(self.headers)