from core.tests import BaseTestCase
from notifications.models import Notification
from posts.models import Post


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
