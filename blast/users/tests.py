import json

from django.test import TestCase
from django.core.urlresolvers import reverse_lazy, reverse
from django.test.client import MULTIPART_CONTENT
from django.utils import timezone
from rest_framework import status

from smsconfirmation.models import PhoneConfirmation
from users.models import User, UserSettings
from core.tests import BaseTestCase, BaseTestCaseUnauth, create_file


class CheckUsernameAndPasswordTest(BaseTestCase):

    url = reverse_lazy('user-list') + 'check/'

    def test_taken_phone_and_username(self):
        data = {
            'username': self.username,
            'phone': self.phone
        }

        response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('phone')[0], 'This phone is taken')
        self.assertEqual(response.data.get('username')[0], 'This username is taken')

    def test_taken_phone(self):
        data = {
            'username': self.username + '_555',
            'phone': self.phone
        }

        response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('phone'))
        self.assertIsNone(response.data.get('username'))

    def test_untaken_phone_and_username(self):
        data = {
            'username': self.username + '_555',
            'phone': self.phone + '999'
        }

        response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RegisterTest(TestCase):

    fixtures = ('countries',)
    url = reverse_lazy('user-list')
    phone = '+79521234567'
    username = 'username'
    password = 'password123'
    country = 1

    def setUp(self):
        self.confirmation = PhoneConfirmation.objects.create(phone=self.phone,
                                                             is_confirmed=True,
                                                             request_type=PhoneConfirmation.REQUEST_PHONE)
    def test_user_unconfirmed_phone(self):
        data = {
            'phone': self.phone + '1',
            'username': self.username,
            'password': self.password,
            'country': self.country
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # TODO: Check that user does not exist

    def test_user_register(self):
        """Should register user"""
        data = {
            'phone': self.phone,
            'username': self.username,
            'password': self.password,
            'country': self.country,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(phone=self.phone)

        self.assertEqual(self.phone, user.phone)
        self.assertEqual(self.username, user.username)
        self.assertTrue(user.check_password(self.password))

        # Check user settings
        settings = UserSettings.objects.get(user=user)

        # Useless assert
        self.assertEqual(settings.user.pk, user.pk)

    def test_min_password_length(self):
        """Checks that password length greater or equal 6"""

        data = {
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
        # avatar = create_file('avatar.png', False)
        data = {
            'bio': self.bio,
            'website': self.website,
            'fullname': self.fullname,
            'is_private': not self.user.is_private,
            'is_safe_mode': not self.user.is_safe_mode,
            'avatar': None,
            'save_original_content': not self.user.save_original_content
        }

        response = self.client.patch(self.url, json.dumps(data),
                                     content_type='application/json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.bio, self.bio)
        self.assertEqual(self.user.avatar.name, '')
        self.assertEqual(self.user.website, self.website)
        self.assertEqual(self.user.is_private, data['is_private'])
        self.assertEqual(self.user.is_safe_mode, data['is_safe_mode'])
        self.assertEqual(self.user.save_original_content, data['save_original_content'])
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


class TestResetPasswordAuthorized(BaseTestCase):
    """Test case for authorized user"""

    url = reverse_lazy('user-password-auth')
    new_password = 'new_password'

    def test_change_password(self):
        data = {
            'old_password': self.password,
            'password1': self.new_password,
            'password2': self.new_password
        }

        response = self.patch_json(self.url, data)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(self.new_password))


class TestChangePhoneNumber(BaseTestCase):
    url = reverse_lazy('user-phone')
    new_phone = '+79551234567'

    def setUp(self):
        super().setUp()

        PhoneConfirmation.objects.create(phone=self.new_phone, is_confirmed=True,
                                         request_type=PhoneConfirmation.REQUEST_PHONE)

    def test_change_phone(self):
        # TODO: Check "bad" cases
        data = {
            'password': self.password,
            'current_phone': self.phone,
            'new_phone': self.new_phone,
        }

        response = self.patch_json(self.url, data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.phone, self.new_phone)

    def test_change_unconfirmed_phone(self):
        data = {
            'passwrod': self.password,
            'current_phone': self.phone + '1',
            'new_phone': self.new_phone + '1'
        }

        response = self.patch_json(self.url, data)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user.phone, self.phone)

    def test_change_phone_taken_number(self):
        phone = self.phone + '1'
        User.objects.create_user(username=self.username + '1', phone=phone, password=self.password)
        data = {
            'password': self.password,
            'current_phone': self.phone,
            'new_phone': phone
        }

        response = self.patch_json(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('new_phone'))


class TestUserSettings(BaseTestCase):

    def test_user_settings(self):
        url = reverse_lazy('user-settings')

        settings = UserSettings.objects.get(user=self.user)
        data = {
            'notify_my_blasts': not settings.notify_my_blasts,
            'notify_upvoted_blasts': not settings.notify_upvoted_blasts,
            'notify_downvoted_blasts': not settings.notify_downvoted_blasts,
            'notify_pinned_blasts': not settings.notify_pinned_blasts,

            'notify_votes': not settings.notify_votes,

            'notify_new_followers': UserSettings.OFF,
            'notify_comments': UserSettings.OFF,
            'notify_reblasts': UserSettings.EVERYONE,
        }

        response = self.patch_json(url, data)

        settings.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(settings.notify_my_blasts, data['notify_my_blasts'])
        self.assertEquals(settings.notify_upvoted_blasts, data['notify_upvoted_blasts'])
        self.assertEquals(settings.notify_downvoted_blasts, data['notify_downvoted_blasts'])
        self.assertEquals(settings.notify_pinned_blasts, data['notify_pinned_blasts'])
        self.assertEquals(settings.notify_votes, data['notify_votes'])
        self.assertEquals(settings.notify_new_followers, data['notify_new_followers'])
        self.assertEquals(settings.notify_comments, data['notify_comments'])
        self.assertEquals(settings.notify_reblasts, data['notify_reblasts'])


class TestUserFollower(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.other = User.objects.create_user(username='other_user',
            password=self.password, phone='-7')

    def test_user_follow(self):
        url = reverse_lazy('user-detail', kwargs={'pk': self.other.pk})

        response = self.client.put(url + 'follow/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.other.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.other.followers.count(), 1)
        self.assertEqual(self.user.followees.count(), 1)

        # Check user list
        url = reverse_lazy('user-list')

        response = self.client.get(url)
        users = {it['id']: it for it in response.data['results']}

        user = users[self.user.pk]
        other = users[self.other.pk]

        self.assertEqual(user['followers'], 0)
        self.assertEqual(user['following'], 1)

        self.assertEqual(other['followers'], 1)
        self.assertEqual(other['following'], 0)