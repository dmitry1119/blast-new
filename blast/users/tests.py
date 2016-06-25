from django.test import TestCase
from django.core.urlresolvers import reverse_lazy
from rest_framework import status
from users.models import User


class RegisterTest(TestCase):

    url = reverse_lazy('user-list')

    def setUp(self):
        pass

    def test_min_password_length(self):
        """Checks that password length greater or equal 6"""

        data = {
            'phone': '9131234567',
            'username': 'bob_dilan',
            'password': '1234',
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('errors').get('password'))

    def test_empty_password(self):
        data = {
            'phone': '9131234567',
            'username': 'bob_dilan'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('errors').get('password'))

    def test_username_max_length(self):
        """Checks that username length less than 15"""
        data = {
            'phone': '9131234567',
            'username': 'string'*10,
            'password': 'cool_password'
        }

        response = self.client.post(self.url, data)
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('errors').get('username'))

    def test_register_user(self):
        """Should register user."""
        data = {
            'phone': '913123456',
            'username': 'batman',
            'password': '123456'
        }

        response = self.client.post(self.url, data)
        user = User.objects.get(phone=data['phone'], username=data['username'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data.get('user_id'))
        self.assertEqual(user.phone, data['phone'])

