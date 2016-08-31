from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from rest_framework import status

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


class TagSearchTest(BaseTestCase):

    url = reverse_lazy('tag-search')

    def setUp(self):
        super().setUp()
        #
        # posts = []
        # for it in range(10):
        #     posts.append(Post(user=self.user, text='post with @hashtag {}'.format(it)))
        #
        # Post.objects.create(posts)
        # self.posts = Post.objects.all()
        # for it in range(3):
        #     self.user.pinned_posts.add(self.posts[it])

    def test_tag_search(self):
        pass
        # url = self.url + '?title={}'.format('hashtag')
        # response = self.client.get(self.url)
        #
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        #
        # result = response.data['result']
        # self.assertEqual(len(result), 10)
        #
        # # TODO: Check first free is pinned posts.


class TagPinnedSearch(BaseTestCase):

    tag_count = 10

    def setUp(self):
        super().setUp()

        tags = [Tag(title='tag{}'.format(it)) for it in range(TagPinnedSearch.tag_count)]
        Tag.objects.bulk_create(tags)

    def test_pin_tag(self):
        index = TagPinnedSearch.tag_count // 2
        title = 'tag{}'.format(index)
        url = reverse_lazy('tag-detail', kwargs={'pk': title})
        url += 'pin/'

        response = self.put_json(url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()

        self.assertEqual(self.user.pinned_tags.count(), 1)
        self.assertTrue(self.user.pinned_tags.filter(title=title))

    def test_unpin_tag(self):
        tag = Tag.objects.get(title='tag5')

        self.user.pinned_tags.add(tag)

        url = reverse_lazy('tag-detail', kwargs={'pk': tag.title})
        url += 'unpin/'

        response = self.put_json(url, {})
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.pinned_tags.count(), 0)
