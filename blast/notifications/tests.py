from django.core.urlresolvers import reverse_lazy
from rest_framework import status

from core.tests import BaseTestCase
from notifications.models import Notification
from posts.models import Post
from users.models import User


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
            self.assertEqual(notification.text, Notification.VOTES_REACHED_PATTERN.format(it))

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
            self.assertEqual(notification.text, Notification.VOTES_REACHED_PATTERN.format(it))


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
