from django.core.urlresolvers import reverse_lazy
from rest_framework import status

from core.tests import BaseTestCase, BaseTestCaseUnauth
from smsconfirmation.models import PhoneConfirmation


class TestPhoneConfirmation(BaseTestCase):

    url = reverse_lazy('phone-confirmation')
    phone = '+79991234567'

    def test_get_confirmation_code(self):
        response = self.client.post(self.url, data={'phone': self.phone})

        confirm = PhoneConfirmation.objects.get(phone=self.phone)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(confirm.is_confirmed)


class TestResetPassword(BaseTestCaseUnauth):
    fixtures = ('countries.json', )

    url = reverse_lazy('reset-password')

    def setUp(self):
        super().setUp()

        self.client.post(self.url, data={'phone': self.user.phone})
        self.password_request = PhoneConfirmation.objects.get(phone=self.user.phone,
                                                              request_type=PhoneConfirmation.REQUEST_PASSWORD)

    def test_code_not_found(self):
        data = {
            'code': 'abcd',
            'phone': '1234567',
            'password1': 'newpass',
            'password2': 'newpass'
        }

        response = self.patch_json(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIsNotNone(response.data.get('code'))
        self.assertIsInstance(response.data.get('code'), list)

    def test_invalid_code(self):
        data = {
            'code': 'abcd',
            'phone': self.user.phone,
            'password1': 'password',
            'password2': 'password'
        }

        response = self.patch_json(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('code'))
        self.assertIsInstance(response.data.get('code'), list)

    def test_wrong_password_len(self):
        data = {
            'code': self.password_request.code,
            'phone': self.user.phone,
            'password1': 'new',
            'password2': 'new'
        }

        response = self.patch_json(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.check_password(self.password))
        self.assertFalse(self.password_request.is_confirmed)

    def test_password_do_not_match(self):
        data = {
            'code': self.password_request.code,
            'phone': self.user.phone,
            'password1': 'old_password',
            'password2': 'new_password'
        }

        response = self.patch_json(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.check_password(self.password))
        self.assertFalse(self.password_request.is_confirmed)

    def test_change_password(self):
        new_password = 'new_password'
        data = {
            'code': self.password_request.code,
            'phone': self.user.phone,
            'password1': new_password,
            'password2': new_password,
        }

        response = self.patch_json(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.password_request.is_confirmed)
        self.assertTrue(self.user.check_password(new_password))
        self.assertIsNone(response.data.get('errors'))

    def test_two_confirmation_requests(self):
        self.client.post(self.url, data={'phone': self.user.phone})

        confirmations = PhoneConfirmation.objects.get_actual(phone=self.phone,
                                                             request_type=PhoneConfirmation.REQUEST_PASSWORD)

        new_password = 'new_password'
        data = {
            'code': confirmations.code,
            'phone': self.user.phone,
            'password1': new_password,
            'password2': new_password,
        }

        self.patch_json(self.url, data)

        self.user.refresh_from_db()
        self.password_request.refresh_from_db()

        self.assertFalse(self.password_request.is_confirmed)
        self.assertTrue(self.user.check_password(new_password))
