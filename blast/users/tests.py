import json

from django.test import TestCase
from django.core.urlresolvers import reverse_lazy
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
        """
        Should return 404 for user that tries to edit not his profile.
        """
        response = self.client.patch(self.url, json.dumps({
            'bio': 'new bio',
            'website': 'new website'
        }), content_type='application/json')

        self.other_user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.other_user.bio, '')
        self.assertEqual(self.other_user.website, '')


class UpdateProfilePermissionsTest(BaseTestCaseUnauth):

    def test_edit_access(self):
        """
        Should return 404 for user which try to edit not his profile.
        """
        response = self.client.patch(self.url, json.dumps({
            'bio': 'new bio',
            'website': 'new website'
        }), content_type='application/json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.user.bio, '')
        self.assertEqual(self.user.website, '')

    def setUp(self):
        super().setUp()
        self.url = reverse_lazy('user-detail', kwargs={
            'pk': self.user.pk
        })


class UpdateProfileTest(BaseTestCase):

    bio = 'user bio text'
    website = 'www.google.com'
    fullname = 'Tiler'
    birthday = timezone.now()

    def setUp(self):
        super().setUp()

        self.url = reverse_lazy('user-detail', kwargs={
            'pk': self.user.pk
        })

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