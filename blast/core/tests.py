import json

from django.test import TestCase
from django.core.urlresolvers import reverse_lazy

from users.models import User


class BaseTestCaseUnauth(TestCase):
    fixtures = ('countries.json',)

    phone = '8913123123'
    country = 1
    password = '111111'
    username = 'username'

    def setUp(self):
        data = {
            'phone': self.phone,
            'username': self.username,
            'password': self.password,
            'country': self.country
        }

        self.client.post(reverse_lazy('user-list'), data)
        self.user = User.objects.get(username=self.username)

        data = {
            'phone': self.phone,
            'password': self.password
        }

        response = self.client.post(reverse_lazy('get-auth-token'), data)
        self.auth_token = response.data.get('token')

    def patch_json(self, url, data):
        return self.client.patch(url, json.dumps(data), content_type='application/json')


class BaseTestCase(BaseTestCaseUnauth):

    def setUp(self):
        super().setUp()

        self.headers = {
            'HTTP_AUTHORIZATION': 'JWT {0}'.format(self.auth_token)
        }
        self.client.defaults.update(self.headers)