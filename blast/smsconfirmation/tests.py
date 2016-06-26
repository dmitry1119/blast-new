import json
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase

from rest_framework import status

from smsconfirmation.models import PhoneConfirmation, get_phone_confirmation_code
from users.models import User


class Test(TestCase):

    fixtures = ('countries.json',)

    phone = '8913123123'
    country = 1
    password = '111111'
    username = 'username'

    url = reverse_lazy('phone-confirmation')

    def setUp(self):
        """Should register user."""
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
        self.headers = {
            'HTTP_AUTHORIZATION': 'JWT {0}'.format(self.auth_token)
        }
        self.client.defaults.update(self.headers)

    def test_empty_code(self):
        response = self.client.post(self.url, {
            'code': None
        })

        confirm = PhoneConfirmation.objects.get(user=self.user)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(confirm.is_confirmed)
        self.assertFalse(self.user.is_confirm)

    def test_invalid_code(self):
        response = self.client.post(self.url, {
            'code': 'abcd'
        })

        confirm = PhoneConfirmation.objects.get(user=self.user)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(confirm.is_confirmed)
        self.assertFalse(self.user.is_confirm)

    def test_valid_code(self):
        confirm = PhoneConfirmation.objects.get(user=self.user)
        self.client.post(self.url, {'code': confirm.code})

        confirm.refresh_from_db()
        self.user.refresh_from_db()

        self.assertTrue(confirm.is_confirmed)
        self.assertTrue(self.user.is_confirm)