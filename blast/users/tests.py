import json
from django.test import TestCase
from django.core.urlresolvers import reverse_lazy
from django.test.client import MULTIPART_CONTENT
from rest_framework import status
from smsconfirmation.models import PhoneConfirmation
from users.models import User

from core.tests import BaseTestCase

class RegisterTest(TestCase):

    fixtures = ('countries',)
    url = reverse_lazy('user-list')
    phone = '9521234567'

    def setUp(self):
        self.country = 1
        pass

    def test_min_password_length(self):
        """Checks that password length greater or equal 6"""

        data = {
            'phone': self.phone,
            'username': 'bob_dilan',
            'password': '1234',
            'country': self.country
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('errors').get('password'))

    def test_empty_password(self):
        data = {
            'phone': self.phone,
            'username': 'bob_dilan',
            'country': self.country
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('errors').get('password'))

    def test_username_max_length(self):
        """Checks that username length less than 15"""
        data = {
            'phone': self.phone,
            'username': 'string'*10,
            'password': 'cool_password',
            'country': self.country
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('errors').get('username'))

    def test_register_user(self):
        """Should register user."""
        data = {
            'phone': self.phone,
            'username': 'batman',
            'password': '123456',
            'country': self.country
        }

        response = self.client.post(self.url, data)
        user = User.objects.get(phone=data['phone'], username=data['username'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data.get('user_id'))
        self.assertEqual(user.phone, data['phone'])
        self.assertEqual(user.country.pk, data['country'])

        confirmation = PhoneConfirmation.objects.get(user=user)

        self.assertFalse(confirmation.is_confirmed)
        self.assertFalse(confirmation.is_delivered)


class UpdateProfileAccessTest(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.other_user = User.objects.create_user(username='username-01',
                                                   password='password',
                                                   phone='987654321')

        self.url = reverse_lazy('user-detail', kwargs={
            'pk': self.other_user.pk
        })

    def test_edit_access(self):
        response = self.client.patch(self.url, json.dumps({
            'bio': 'new bio',
            'website': 'new website'
        }), content_type='application/json')

        print('CODE', response.status_code, response.data)

        self.other_user.refresh_from_db()
        print ('BIO', self.other_user.bio)


class UpdateProfileTest(BaseTestCase):

    def setUp(self):
        super().setUp()

        self.url = reverse_lazy('user-detail', kwargs={
            'pk': self.user.pk
        })

    def test_edit_access(self):
        pass

    def test_edit_bio_and_website(self):
        pass