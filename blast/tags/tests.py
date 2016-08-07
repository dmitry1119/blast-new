from django.test import TestCase

from core.tests import BaseTestCase
from posts.models import Post
from tags.models import Tag


class PostTagsTest(BaseTestCase):
    text = u'Post text with #hashtag1, #hashtag2, #hashtag3'

    def setUp(self):
        super().setUp()
        Tag.objects.create(title='hashtag1')

    def test_post_tags(self):
        post = Post.objects.create(text=self.text,
                                   user=self.user)

        tags = Tag.objects.all()

        self.assertEqual(len(tags), 3)
        self.assertEqual(len(post.tags.all()), 3)

        titles = [it.title for it in tags]
        self.assertIn('hashtag1', titles)
        self.assertIn('hashtag2', titles)
        self.assertIn('hashtag3', titles)

        for it in tags:
            self.assertEqual(it.total_posts, 1)

    def test_post_deleted(self):
        total = 5

        for it in range(total):
            Post.objects.create(text=self.text, user=self.user)

        tags = Tag.objects.all()
        for it in tags:
            self.assertEqual(it.total_posts, total)

        Post.objects.first().delete()

        tags = Tag.objects.all()
        for it in tags:
            self.assertEqual(it.total_posts, total - 1)

        Post.objects.all().delete()
        tags = Tag.objects.all()

        self.assertEqual(len(tags), 3)
        for it in tags:
            self.assertEqual(it.total_posts, 0)