from typing import List

from posts.models import PostVote
from users.models import User


# TODO: It uses in PostComment.list method and should be refactored.
def attach_users(items: list, user: User, request):
    """
    Attaches user to post dictionary
    :param items: list of post dictionaries
    :return: modified list of items
    """
    if len(items) == 0:
        return items

    users = {it['user'] for it in items if it['user']}
    users = User.objects.filter(pk__in=users)
    users = {it.pk: it for it in users}

    for post in items:
        author = {}

        if not post['user']:
            author['username'] = 'Anonymous'
            author['avatar'] = None
        else:
            user = users[post['user']]
            author['username'] = user.username
            author['id'] = user.pk
            if user.avatar:
                author['avatar'] = request.build_absolute_uri(user.avatar.url)
            else:
                author['avatar'] = None
        post['author'] = author

    return items


def mark_voted(posts: List, user: User):
    if user.is_anonymous() or len(posts) == 0:
        return posts

    ids = {it['id'] for it in posts}
    votes = list(PostVote.objects.filter(post_id__in=ids, user=user))
    votes = {it.post_id: it.is_positive for it in votes}

    for post in posts:
        pk = post['id']
        post['is_upvoted'] = pk in votes and votes[pk] == True
        post['is_downvoted'] = pk in votes and votes[pk] == False

    return posts


def mark_pinned(posts: list, user: User):
    # TODO (VM): Make test
    """
    Adds is_pinned flag to each post dictionary in posts list
    :return: modified list of posts
    """
    if user.is_anonymous() or len(posts) == 0:
        return posts

    ids = [it['id'] for it in posts]
    pinned = user.pinned_posts.filter(id__in=ids).values('id')
    pinned = [it['id'] for it in pinned]

    for post in posts:
        if post['id'] in pinned:
            post['is_pinned'] = True
        else:
            post['is_pinned'] = False

    return posts


def extend_posts(posts: list, user: User, request):
    """
    Adds additional information to raw posts
    :param posts: list of dictionaries
    :return: modified posts list
    """
    data = mark_pinned(posts, user)
    data = attach_users(data, user, request)
    data = mark_voted(posts, user)

    return data