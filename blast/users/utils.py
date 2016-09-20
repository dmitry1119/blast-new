from users.models import User
from posts.models import Post

from typing import List, Set


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
