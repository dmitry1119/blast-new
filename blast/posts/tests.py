from io import BytesIO

from PIL import Image
from django.test import TestCase
from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from rest_framework import status

from core.tests import BaseTestCase
from users.models import User
from posts.models import Post, PostComment


def crete_file(name, content_file=True):
    image = Image.new('RGBA', size=(50, 50))
    file = BytesIO(image.tostring())
    file.name = name
    file.seek(0)

    if content_file:
        return ContentFile(file.read(), name=name)
    else:
        return SimpleUploadedFile(name, file.read(), content_type='image/png')


class AnyPermissionTest(TestCase):
    """
    Permissions test for unauthorized user
    """

    fixtures = ('countries.json',)

    def setUp(self):
        user = User.objects.create_user(phone='+1234567', password='123456', username='username')

        file = crete_file('test.png')
        self.post = Post.objects.create(user=user, text='some_text', video=file)

    def test_any_view_posts(self):
        url = reverse_lazy('post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_any_create_post(self):
        url = reverse_lazy('post-list')
        response = self.client.post(url, data={
            'video': crete_file('test_01.png'),
            'user': 1,
            'text': 'spam'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)

    def test_any_delete_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)


class PostTest(BaseTestCase):
    def setUp(self):
        super().setUp()

        file = crete_file('test.png')
        self.post = Post.objects.create(user=self.user, text='some_text', video=file)

    def test_hide_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        response = self.patch_json(url + 'hide/')
        self.post.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.post.is_hidden)

        response = self.patch_json(url + 'show/')
        self.post.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.post.is_hidden)

    def test_delete_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        self.client.delete(url, content_type='application/json')

        self.assertEqual(Post.objects.all().count(), 0)


class CommentTest(BaseTestCase):
    url = reverse_lazy('comment-list')

    def setUp(self):
        super().setUp()
        file = crete_file('filename.txt')
        self.post = Post.objects.create(video=file, user=self.user, text='text')

    def test_create_comment(self):
        text = 'comment text'
        response = self.client.post(self.url, data={
            'post': self.post.pk,
            'text': text
        })

        comment = PostComment.objects.get(user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comment.text, text)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.post)

    # TODO: Check permissions on delete method
    def test_delete_comment(self):
        text = 'comment text'
        comment = PostComment.objects.create(post=self.post, user=self.user, text=text)

        url = reverse_lazy('comment-detail', kwargs={'pk': comment.pk})
        self.client.delete(url, content_type='application/json')

        self.assertEqual(PostComment.objects.filter(post=self.post, user=self.user).count(), 0)


class AuthorizedPermissionsTest(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user2 = User.objects.create_user(phone='+1231231',
                                              password='123456',
                                              username='user2')

        file = crete_file('test.png')
        self.post = Post.objects.create(user=self.user2, text='some text', video=file)

    def test_other_get_posts(self):
        url = reverse_lazy('post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_authorized_create_post(self):
        url = reverse_lazy('post-list')

        video = crete_file('test.png', False)

        response = self.client.post(url, data={
            'video': video,
            'user': self.user.pk,
            'text': 'text'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)

    def test_authorized_delete_post(self):
        """
        self.user cannot delete post of self.user2
        """
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)

    def test_vote_post(self):

        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        response = self.put_json(url + 'vote/')
        self.post.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.post.votes_count(), 1)
        self.assertEqual(self.post.downvoted_count(), 0)

        response = self.put_json(url + 'downvote/')
        self.post.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.votes_count(), 0)
        self.assertEqual(self.post.downvoted_count(), 1)

    def test_hide_permissions_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        response = self.patch_json(url + 'hide/')
        self.post.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(self.post.is_hidden)
