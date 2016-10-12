import json

from django.core.urlresolvers import reverse_lazy
from rest_framework import status

from core.tests import BaseTestCase
from notifications.models import Notification, FollowRequest
from posts.models import Post
from users.models import User, UserSettings, Follower


class TestPostVotesNotification(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_post_votes_notification(self):
        notify_counter = range(10, 101, 10)
        for it in notify_counter:
            Post.objects.create(user=self.user, voted_count=it)

        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 10)
        for notification, it in zip(notifications, notify_counter):
            self.assertEqual(notification.text, Notification.TEXT_VOTES_REACHED_PATTERN.format(it))

        # Checks that Notification creates only for votes which
        # less or equal then 100 and dived by 10
        Post.objects.create(user=self.user, voted_count=150)
        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 10)

    def test_post_votes_large_votes_notification(self):
        """Checks that Notification creates for each 1000 votes"""
        notify_counter = range(500, 10001, 500)

        for it in notify_counter:
            Post.objects.create(user=self.user, voted_count=it)

        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 10)
        for notification, it in zip(notifications, range(1000, 10001, 1000)):
            self.assertEqual(notification.text, Notification.TEXT_VOTES_REACHED_PATTERN.format(it))


class TestPostUserNotification(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.other = User.objects.create_user(phone='123', password='password',
                                              country=self.country, username='other')

    def test_post_noticed_notification(self):
        self.other.settings.notify_comments = UserSettings.EVERYONE
        self.other.settings.save()

        self.post = Post.objects.create(text='@{}, hello!'.format(self.other.username),
                                        user=self.user)

        self.assertEqual(Notification.objects.count(), 1)

        notification = Notification.objects.get(post=self.post)
        self.assertEqual(notification.post, self.post)
        self.assertEqual(notification.user, self.other)
        self.assertEqual(notification.other, self.user)
        self.assertEqual(notification.type, Notification.MENTIONED_IN_COMMENT)

    def test_post_notices_by_follower(self):
        Follower.objects.create(followee=self.user, follower=self.other)
        self.post = Post.objects.create(text='@{}, hello!'.format(self.other.username),
                                        user=self.user)

        qs = Notification.objects.filter(type=Notification.MENTIONED_IN_COMMENT)
        self.assertEqual(qs.count(), 1)

        notification = Notification.objects.get(post=self.post)

        self.assertEqual(notification.post, self.post)
        self.assertEqual(notification.user, self.other)
        self.assertEqual(notification.other, self.user)
        self.assertEqual(notification.type, Notification.MENTIONED_IN_COMMENT)


class TestFollowingNotification(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.other = User.objects.create_user(phone='123', password='123',
                                              username='other', country=self.country)

    def test_following_notification(self):
        """Should create following notification for self.other user"""
        url = reverse_lazy('user-detail', kwargs={'pk': self.other.pk})
        url += 'follow/'

        response = self.put_json(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = Notification.objects.all()
        notifications = list(notifications)
        self.assertEqual(len(notifications), 1)

        # User self.user started following from self.other
        # and self.other got notification
        notification = notifications[0]
        self.assertEqual(notification.user.pk, self.other.pk)
        self.assertEqual(notification.other.pk, self.user.pk)


class TestFollowRequest(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.private_user = User.objects.create_user(phone='123', password='123',
                                                     username='private_user', country=self.country)
        self.private_user.is_private = True
        self.private_user.save()

    def test_follow_request(self):
        url = reverse_lazy('user-detail', kwargs={'pk': self.private_user.pk})
        url += 'follow/'

        response = self.put_json(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(FollowRequest.objects.count(), 1)
        self.assertTrue(FollowRequest.objects.filter(followee=self.private_user,
                                                     follower=self.user).exists())

    def test_follow_request_accept(self):
        self.user.is_private = True
        self.user.save()

        follow_request = FollowRequest.objects.create(followee=self.user,
                                                      follower=self.private_user)
        # Accept confirmation
        url = reverse_lazy('followrequest-detail', kwargs={'pk': follow_request.pk})
        response = self.put_json(url, json.dumps({'accept': True}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Follower.objects.filter(followee=self.user,
                                                follower=self.private_user).exists())

    def test_follow_request_reject(self):
        self.user.is_private = True
        self.user.save()

        follow_request = FollowRequest.objects.create(followee=self.user,
                                                      follower=self.private_user)
        # Confirm
        url = reverse_lazy('followrequest-detail', kwargs={'pk': follow_request.pk})
        response = self.put_json(url, json.dumps({'accept': False}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follower.objects.filter(followee=self.private_user).exists())
        self.assertFalse(Follower.objects.filter(followee=self.private_user).exists())
        self.assertFalse(FollowRequest.objects.filter(followee=self.user.pk,
                                                      follower=self.private_user.pk).exists())
