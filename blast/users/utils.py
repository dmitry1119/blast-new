from notifications.models import FollowRequest
from users.models import User, Follower
from posts.models import Post

from typing import List, Set, Dict


def filter_followee_users(user: User, user_ids: list or set):
    if not user.is_authenticated():
        return set()

    result = Follower.objects.filter(follower=user,
                                     followee_id__in=user_ids).values_list('followee_id', flat=True)
    return set(result)


def mark_followee(users: List[Dict], user: User) -> List[Dict]:
    if not user.is_authenticated():
        return users

    followees = filter_followee_users(user, {it['id'] for it in users})
    for it in users:
        pk = it['id']
        it['is_followee'] = pk in followees


def mark_requested(users: List[Dict], user: User) -> List[Dict]:
    if not user.is_authenticated():
        return users

    requests = FollowRequest.objects.filter(follower=user, followee_id__in={it['id'] for it in users})
    requests = set(requests.values_list('followee_id', flat=True))
    for it in users:
        it['is_requested'] = it['id'] in requests

    return users


def bound_posts_to_users(user_ids: List[int] or Set[int], n: int):
    """Returns dict of lists of last n posts for each user in user_ids"""
    users_to_posts = {}
    posts = []
    for user in user_ids:
        user_posts_ids = User.get_posts(user, 0, n-1)
        users_to_posts[user] = user_posts_ids
        posts.extend(user_posts_ids)

    # Pulls posts from db and builds in-memory index
    posts = Post.objects.actual().filter(pk__in=posts)
    posts = {it.pk: it for it in posts}

    results = {}
    for user in user_ids:
        user_posts_ids = users_to_posts[user]
        results[user] = [v for (k, v) in posts.items() if k in user_posts_ids]

    return results
