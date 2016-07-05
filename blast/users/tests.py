import json

from django.test import TestCase
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils import timezone
from rest_framework import status

from smsconfirmation.models import PhoneConfirmation
from users.models import User
from core.tests import BaseTestCase, BaseTestCaseUnauth


class RegisterTest(TestCase):

    fixtures = ('countries',)
    url = reverse_lazy('user-list')
    phone = '+79521234567'
    username = 'username'
    password = 'password123'
    country = 1

    def setUp(self):
        self.confirmation = PhoneConfirmation.objects.create(phone=self.phone,
                                                             request_type=PhoneConfirmation.REQUEST_PHONE)

    def test_user_register(self):
        """Should register user"""
        data = {
            'phone': self.phone,
            'username': self.username,
            'password': self.password,
            'country': self.country,
            'code': self.confirmation.code
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(phone=self.phone)

        self.assertEqual(self.phone, user.phone)
        self.assertEqual(self.username, user.username)
        self.assertTrue(user.check_password(self.password))

    def test_min_password_length(self):
        """Checks that password length greater or equal 6"""

        data = {
            'code': self.confirmation.code,
            'phone': self.phone,
            'username': self.username,
            'password': '1234',
            'country': self.country
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_password(self):
        data = {
            'phone': self.phone,
            'username': 'bob_dilan',
            'country': self.country
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_max_length(self):
        """Checks that username length less than 15"""
        data = {
            'phone': self.phone,
            'username': 'string'*10,
            'password': 'cool_password',
            'country': self.country
        }

        response = self.client.post(self.url, data)

        user = None
        try:
            user = User.objects.get(phone=self.phone)
        except User.DoesNotExist:
            pass

        self.assertIsNone(user)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateProfileTest(BaseTestCase):

    bio = 'user bio text'
    website = 'www.google.com'
    fullname = 'Tiler'
    birthday = timezone.now()

    def setUp(self):
        super().setUp()

        self.url = reverse('user-profile')

    def test_edit_optional_data(self):
        data = json.dumps({
            'bio': self.bio,
            'website': self.website,
            'fullname': self.fullname,
        })

        response = self.client.patch(self.url, data, content_type='application/json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.bio, self.bio)
        self.assertEqual(self.user.website, self.website)
        self.assertEqual(self.user.fullname, self.fullname)

    def test_edit_private_data(self):
        data = json.dumps({
            'birthday': str(self.birthday),
            'gender': User.GENDER_FEMALE,
        })

        response = self.client.patch(self.url, data, content_type='application/json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.gender, User.GENDER_FEMALE)
        self.assertEqual(self.user.birthday, self.birthday)