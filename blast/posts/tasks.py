import logging
from datetime import timedelta

import itertools

import redis
from django.utils import timezone

from push_notifications.apns import apns_send_bulk_message
from push_notifications.models import APNSDevice

from celery import shared_task
from posts.models import Post, PostVote
from users.models import User


logger = logging.getLogger(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


@shared_task(bind=False)
def clear_expired_posts():
    posts = Post.objects.expired()

    posts = list(posts)
    if not len(posts):
        return

    logger.info('Remove {} expired posts'.format(len(posts)))

    for it in posts:
        logger.info('Delete {}'.format(it.pk))
        # TODO: delete file
        it.delete()


def send_ending_soon_notification(post_id: int, users: set):
    expire_s = 60 * 10  # 10 minutes
    send_marker_key = 'EndSoonPUSHSendState:{}:{}'.format(post_id, '{}')

    logger.info('Send ending soon PUSH message for {} to {}'.format(post_id, users))

    to_send = [it for it in users if not r.exists(send_marker_key.format(it))]

    # TODO: send push

    logger.info('Set up ending soon markers for {} {}'.format(post_id, to_send))
    for it in to_send:
        key = send_marker_key.format(it)
        r.set(key, '1', ex=expire_s)


def _get_post_to_users_push_list() -> dict:
    expired_posts = Post.objects.filter(expired_at__lte=timezone.now() + timedelta(minutes=10))
    expired_posts = list(expired_posts.values('id', 'user'))

    if not expired_posts:
        return

    logger.info('Got ready for removal posts: {}'.format(expired_posts))

    # Send push messages to owners
    owner_set = {it['user'] for it in expired_posts}
    owner_set = User.objects.filter(id__in=owner_set, settings__notify_my_blasts=True)
    owner_set = list(owner_set.values_list('id', flat=True))
    logger.info('Got post owners: {}'.format(owner_set))

    # Send push message to voters and downvoters
    expired_ids = {it['id'] for it in expired_posts}
    votes = PostVote.objects.filter(post_id__in=expired_ids)
    votes = list(votes.values('is_positive', 'post_id', 'user_id'))
    logger.info('Got votes {}'.format(votes))

    def map_post_to_users(is_positive: bool) -> dict:
        """
        Maps posts to list of voters
        :return: dict of post_id to set of user_id
        """

        def condition(it):
            return it['is_positive'] == is_positive

        users_ids = {it['user_id'] for it in votes if condition(it)}
        users_ids = User.objects.filter(id__in=users_ids, settings__notify_upvoted_blasts=True)
        users_ids = list(users_ids.values_list('id', flat=True))
        if is_positive:
            logger.info('Got post voters: {}'.format(users_ids))
        else:
            logger.info('Got post downvoters: {}'.format(users_ids))

        _votes = (it for it in votes if it['is_positive'] == is_positive)
        _groups = itertools.groupby(_votes, lambda it: it['post_id'])
        _groups = {p: {it['user_id'] for it in g} for p, g in _groups}

        logger.debug('map_post_to_user: {}'.format(_groups))
        return _groups

    post_to_votes = map_post_to_users(True)
    post_to_downvotes = map_post_to_users(False)

    # Merge votes and downvotes list:
    result = {}
    for post_to_users in (post_to_votes, post_to_downvotes):
        for post_id in post_to_users:
            res = set()
            if post_id in post_to_users:
                res |= post_to_users[post_id]

            result[post_id] = res

    # Add post owners to list
    posts = {it['id']: it for it in expired_posts}
    for post_id in posts:
        res = result.get(post_id, set())

        res.add(posts[post_id]['user'])
        result[post_id] = res

    return result


@shared_task(bind=False)
def send_expire_notifications():
    post_to_users = _get_post_to_users_push_list()

    for post_id in post_to_users:
        send_ending_soon_notification(post_id, post_to_users[post_id])

    # for it in
        # APNSDevice.objects.filter(user_id__in=users).send_message('Ending soon', extra={
        #     post_id: expired_posts
        # })

