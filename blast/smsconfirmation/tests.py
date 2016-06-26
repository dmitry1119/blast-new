from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from rest_framework import status
from core.tests import BaseTestCase

from smsconfirmation.models import PhoneConfirmation
from users.models import User


class TestPhoneConfirmation(BaseTestCase):

    url = reverse_lazy('phone-confirmation')

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


class TestResetPassword(BaseTestCase):

    url = reverse_lazy('reset-password')

    def setUp(self):
        super().setUp()

        response = self.client.get(self.url)
        self.password_request = PhoneConfirmation.objects.get(user=self.user,
                                                              request_type=PhoneConfirmation.REQUEST_PASSWORD)

    def test_wrong_password_len(self):
        data = {
            'code': self.password_request.code,
            'password1': 'new',
            'password2': 'new'
        }

        response = self.client.post(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertTrue(self.user.check_password(self.password))
        self.assertFalse(self.password_request.is_confirmed)
        self.assertIsNotNone(response.data.get('errors'))

    def test_password_do_not_match(self):
        data = {
            'code': self.password_request.code,
            'password1': 'old_password',
            'password2': 'new_password'
        }

        response = self.client.post(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertTrue(self.user.check_password(self.password))
        self.assertFalse(self.password_request.is_confirmed)
        self.assertIsNotNone(response.data.get('errors'))

    def test_change_password(self):
        new_password = 'new_password'
        data = {
            'code': self.password_request.code,
            'password1': new_password,
            'password2': new_password,
        }

        response = self.client.post(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertTrue(self.password_request.is_confirmed)
        self.assertTrue(self.user.check_password(new_password))
        self.assertIsNone(response.data.get('errors'))