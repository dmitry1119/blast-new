from django.db import models
from users.models import User


class Notification(models.Model):
    STARTED_FOLLOW = 0
    MENTIONED_IN_COMMENT = 1
    VOTES_REACHED = 2

    TYPE = (
        (STARTED_FOLLOW, 'Started follow'),
        (MENTIONED_IN_COMMENT, 'Mentioned in comment'),
        (VOTES_REACHED, 'Votes reached')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, related_name='notifications')
    other = models.ForeignKey(User, null=True, blank=True, related_name='mention_notifications')

    text = models.CharField(max_length=128)
    type = models.PositiveSmallIntegerField(choices=TYPE)
