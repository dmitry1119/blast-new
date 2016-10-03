import logging

from celery import shared_task
from posts.models import Post


@shared_task(bind=False)
def clear_expired_posts():
    posts = Post.objects.expired()

    posts = list(posts)
    if not len(posts):
        return

    logging.info('Remove {} expired posts'.format(len(posts)))

    for it in posts:
        logging.info('Delete {}'.format(it.pk))
        # TODO: delete file
        it.delete()
