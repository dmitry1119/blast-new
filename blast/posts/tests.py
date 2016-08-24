from datetime import timedelta
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from rest_framework import status

from core.tests import BaseTestCase, create_file
from countries.models import Country
from posts.models import Post, PostComment, PostReport, PostVote
from users.models import User, Follower


class AnyPermissionTest(TestCase):
    """
    Permissions test for unauthorized user
    """

    fixtures = ('countries.json',)

    def setUp(self):
        user = User.objects.create_user(phone='+1234567', password='123456', username='username')

        file = create_file('test.png')
        self.post = Post.objects.create(user=user, video=file)

    def test_any_view_posts(self):
        url = reverse_lazy('post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_any_create_post(self):
        url = reverse_lazy('post-list')
        response = self.client.post(url, data={
            'video': create_file('test_01.png'),
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

        file = create_file('test.png')
        self.post = Post.objects.create(user=self.user, text='some_text', video=file)

    def test_hide_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        response = self.client.put(url + 'hide/', content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.hidden_posts.filter(pk=self.post.pk).exists())

        response = self.client.put(url + 'show/', content_type='application/json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user.hidden_posts.filter(pk=self.post.pk).exists())

    # TODO: Add permission test
    def test_delete_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        self.client.delete(url, content_type='application/json')

        self.assertEqual(Post.objects.all().count(), 0)


class TestAnonymousPost(BaseTestCase):
    def setUp(self):
        super().setUp()

        url = reverse_lazy('post-list')
        response = self.client.post(url, data={
            'video': create_file('test_01.png'),
            'user': self.user.pk,
            'text': 'spam',
            'is_anonymous': True,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post = Post.objects.get(pk=response.data['id'])

    def test_get_anonymous_post(self):
        url = reverse_lazy('post-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['author']['username'], 'Anonymous')
        self.assertEqual(response.data['results'][0]['author']['avatar'], None)

        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['author']['username'], 'Anonymous')
        self.assertEqual(response.data['author']['avatar'], None)

    def test_is_anonymous_post_pinned(self):
        """
        Checks is_anonymous post in pinned list.
        :return:
        """
        self.assertTrue(self.user.pinned_posts.filter(pk=self.post.pk).exists())


class TestIsPinnedPost(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(user=self.user)
        self.user.pinned_posts.add(self.post)

    def test_is_pinned_flag(self):
        url = reverse_lazy('post-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['is_pinned'], True)


class CommentTest(BaseTestCase):
    url = reverse_lazy('comment-list')

    def setUp(self):
        super().setUp()
        file = create_file('filename.txt')
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
        self.assertIsNotNone(response.data.get('author'))

    def test_create_reply_comment(self):
        parent_text = 'parent comment text'
        reply_text = 'reply comment text'
        response = self.client.post(self.url, data={
            'post': self.post.pk,
            'text': parent_text
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], parent_text)
        self.assertEqual(response.data['post'], self.post.pk)

        parent_id = response.data['id']
        response = self.client.post(self.url, data={
            'parent': parent_id,
            'post': self.post.pk,
            'text': reply_text
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url + '?parent=' + str(parent_id))
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['text'], reply_text)

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

        file = create_file('test.png')
        self.post = Post.objects.create(user=self.user2, text='some text', video=file)

    def test_other_get_posts(self):
        url = reverse_lazy('post-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_authorized_create_post(self):
        url = reverse_lazy('post-list')

        video = create_file('test.png', False)

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


class VoteTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(user=self.user)
        self.expired_at = self.post.expired_at

        self.url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

    def test_vote_post(self):
        response = self.put_json(self.url + 'vote/')

        self.post.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.voted_count, 1)
        self.assertEqual(self.post.downvoted_count, 0)
        self.assertEqual(self.post.expired_at, self.expired_at + timedelta(minutes=5))

        url = reverse_lazy('post-list') + 'voted/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results')), 1)

        result = response.data.get('results')[0]
        self.assertEqual(result['id'], self.post.id)
        self.assertEqual(result['author']['username'], self.user.username)

    def test_downvote_post(self):
        response = self.put_json(self.url + 'downvote/')

        self.post.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.voted_count, 0)
        self.assertEqual(self.post.downvoted_count, 1)
        self.assertEqual(self.post.expired_at, self.expired_at - timedelta(minutes=10))

        url = reverse_lazy('post-list') + 'downvoted/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results')), 1)

        result = response.data.get('results')[0]
        self.assertEqual(result['id'], self.post.id)
        self.assertEqual(result['author']['username'], self.user.username)


class ReportTest(BaseTestCase):

    text = 'report text'

    def setUp(self):
        super().setUp()

        video = create_file('test.png', False)

        self.post = Post.objects.create(user=self.user, video=video, text='text')

    def test_custom_report(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk}) + 'report/'
        data = {
            'text': self.text,
            'reason': PostReport.OTHER
        }

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PostReport.objects.count(), 1)

        report = PostReport.objects.get(user=self.user)
        self.assertEqual(report.reason, PostReport.OTHER)


class PinPost(BaseTestCase):

    posts_count = 10

    def setUp(self):
        super().setUp()

        video = create_file('test.png', False)

        self.post = Post.objects.create(user=self.user, video=video, text='text')

    def test_pin_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk}) + 'pin/'

        self.put_json(url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.pinned_posts.count(), 1)

    def test_unpin_post(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})

        self.put_json(url + 'pin/')
        self.user.refresh_from_db()
        self.assertEqual(self.user.pinned_posts.count(), 1)

        self.put_json(url + 'unpin/')
        self.user.refresh_from_db()
        self.assertEqual(self.user.pinned_posts.count(), 0)

    def tes_get_pinned_posts(self):
        url = reverse_lazy('post-list') + '?pinned'

        video = create_file('test.mp4', False)
        for it in range(10):
            Post.objects.create(user=self.user, video=video, text='text')

        self.put_json(reverse_lazy('post-detail', kwargs={'pk': self.post.pk}) + 'pin/')
        self.put_json(url)

        response = self.get(url)
        self.assertEqual(len(response.result), 1)
        self.assertEqual(response.result[0]['pk'], self.post.pk)


class FeedsTest(BaseTestCase):
    url = reverse_lazy('feed-list')

    def setUp(self):
        super().setUp()

        posts = []
        for it in range(10):
            posts.append(Post(user=self.user))

        Post.objects.bulk_create(posts)
        posts = Post.objects.all()
        self.posts = posts

    def test_feeds(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), len(self.posts))

    def test_hidden_post(self):
        self.user.hidden_posts.add(self.posts[5])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.posts)-1)

        should_be_hidden = self.posts[5].pk
        ids = [it['id'] for it in response.data['results']]

        self.assertNotIn(should_be_hidden, ids)

    def test_hide_voted_post(self):
        PostVote.objects.create(user=self.user, post=self.posts[0])

        response = self.client.get(self.url)

        self.assertEqual(len(response.data['results']), len(self.posts)-1)

        should_be_hidden = self.posts[0].pk
        ids = [it['id'] for it in response.data['results']]

        self.assertNotIn(should_be_hidden, ids)

    def test_voted_and_hidden(self):
        PostVote.objects.create(user=self.user, post=self.posts[0])
        self.user.hidden_posts.add(self.posts[1])

        response = self.client.get(self.url)

        self.assertEqual(len(response.data['results']), len(self.posts)-2)

        should_be_hidden = [self.posts[0].pk, self.posts[1]]
        self.assertNotIn(should_be_hidden[0], response.data['results'])
        self.assertNotIn(should_be_hidden[1], response.data['results'])


class VotersList(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(text='some text', user=self.user)

        country = Country.objects.get(pk=1)
        self.user1 = User.objects.create_user(phone='1', username='1', password='1', country=country)
        self.user2 = User.objects.create_user(phone='2', username='2', password='2', country=country)

        PostVote.objects.create(user=self.user,  post=self.post, is_positive=True)
        PostVote.objects.create(user=self.user1, post=self.post, is_positive=True)
        PostVote.objects.create(user=self.user2, post=self.post, is_positive=False)

        Follower.objects.create(follower=self.user, followee=self.user1)
        # self.user.followees.add(self.user1)

    def test_votes_list(self):
        url = reverse_lazy('post-detail', kwargs={'pk': self.post.pk})
        url = url + 'voters/'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        # TODO: Improve and check user[0]
        self.assertEqual(response.data['results'][1]['username'], '1')
        self.assertEqual(response.data['results'][1]['is_followee'], True)