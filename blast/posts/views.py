from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from posts.models import Post, PostComment, PostVote
from posts.serializers import (PostSerializer, PostPublicSerializer,
                               CommentSerializer, CommentPublicSerializer,
                               VoteSerializer, VotePublicSerializer, ReportPostSerializer)

from datetime import timedelta, datetime

from django.conf import settings

from users.models import User


class PerObjectPermissionMixin(object):

    public_serializer_class = None
    private_serializer_class = None

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return self.public_serializer_class
        else:
            return self.private_serializer_class

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return permissions.AllowAny(),
        else:
            return permissions.IsAuthenticated(),

    def check_object_permissions(self, request, obj: Post):
        if request.method in permissions.SAFE_METHODS:
            return

        if obj.user.pk is not request.user.pk:
            return self.permission_denied(self.request, 'You are not owner of this object')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def attach_users(posts: list, user: User, request):
    # TODO (VM): Make test
    """
    Attaches user to post dictionary
    :param posts: list of post dictionaries
    :return: modified list of posts
    """
    if len(posts) == 0:
        return posts

    users = [it['user'] for it in posts]
    users = User.objects.filter(pk__in=users)
    # users = users.values('pk', 'username', 'avatar')
    users = {it.pk: it for it in users}

    for post in posts:
        user = users[post['user']]
        author = {}
        if post.get('is_anonymous'):
            author['username'] = 'Anonymous'
            author['avatar'] = None
            del post['user']
        else:
            author['username'] = user.username
            if user.avatar:
                author['avatar'] = request.build_absolute_uri(user.avatar.url)
            else:
                author['avatar'] = None
        post['author'] = author

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


def fill_posts(posts: list, user: User, request):
    """
    Adds additional information to raw posts
    :param posts: list of dictionaries
    :return: modified posts list
    """
    data = mark_pinned(posts, user)
    data = attach_users(data, user, request)

    return data


class PostsViewSet(PerObjectPermissionMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    ---
    create:
        parameters:
            - name: video
              type: file
            - name: image
              type: file
    """
    queryset = Post.objects.filter(user__is_private=False,
                                   expired_at__gte=datetime.now())  # FIXME(VM): What about private users?

    public_serializer_class = PostPublicSerializer
    private_serializer_class = PostSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        data = fill_posts([serializer.data], self.request.user, request)

        return Response(data[0])

    def list(self, request, *args, **kwargs):
        """
        Returns list of posts without hidden posts.
        ---
        parameters:
            - name: user
              description: filter result by user id
              paramType: query
              type: int
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = fill_posts(serializer.data, request.user, request)
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = fill_posts([serializer.data], request.user, request)

        return Response(data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Changes response use PostPublicSerializer
        data = PostPublicSerializer(serializer.instance).data
        data = fill_posts([data], request.user, request)
        return Response(data[0], status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """
        Deletes user post

        ---
        omit_serializer: true
        parameters:
            - name: pk
              description: user post id
        """
        return super().destroy(request, *args, **kwargs)

    def _update_vote(self, request, is_positive, pk=None,):
        if not self.request.user.is_authenticated():
            return self.permission_denied(self.request, 'You are not authenticated')

        try:
            post = self.queryset.get(pk=pk)
        except Post.DoesNotExist:
            raise Http404()

        vote, created = PostVote.objects.get_or_create(user=request.user, post=post)
        vote.is_positive = is_positive
        vote.save()

        if is_positive:
            post.expired_at += timedelta(minutes=5)
            post.save()
        else:
            post.expired_at -= timedelta(minutes=10)
            post.save()

        status_code = status.HTTP_200_OK

        serializer = VoteSerializer(instance=vote)
        return Response(serializer.data, status=status_code)

    @detail_route(methods=['put'])
    def vote(self, request, pk=None):
        """
        Add vote to post

        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        return self._update_vote(request, True, pk)

    @detail_route(methods=['put'])
    def downvote(self, request, pk=None):
        """
        Downvote post
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        return self._update_vote(request, False, pk)

    def _update_visibility(self, pk, is_hidden):
        post = get_object_or_404(Post, pk=pk)
        user = self.request.user
        exists = user.hidden_posts.filter(pk=post.pk).exists()

        if is_hidden and not exists:
            user.hidden_posts.add(post)

        if not is_hidden and exists:
            user.hidden_posts.remove(post)

        return Response()

    @detail_route(methods=['put'])
    def hide(self, request, pk=None):
        """
        Hide post

        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        return self._update_visibility(pk, True)

    @detail_route(methods=['put'])
    def show(self, request, pk=None):
        """
        Show post

        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        return self._update_visibility(pk, False)

    @detail_route(methods=['post'])
    def report(self, request, pk=None):
        """

        ---
        serializer: posts.serializers.ReportPostSerializer
        parameters:
            - name: pk
              description: post id
              type: query
            - name: reason
              description: OTHER = 0, SENSITIVE_CONTENT = 1, SPAM = 2, DUPLICATED_CONTENT = 3,
                           BULLYING = 4, INTEL_VIOLATION = 5
        """
        if request.user.is_anonymous():
            # TODO: Test this branch
            self.permission_denied(request,
                                   message=getattr(permissions.IsAuthenticated, 'message'))

        instance = get_object_or_404(Post, pk=pk)
        serializer = ReportPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, post=instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['put'])
    def pin(self, request, pk=None):
        """
        Adds post to user pinned posts list
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        if self.request.user.is_anonymous():
            return self.permission_denied(request)
        instance = get_object_or_404(Post, pk=pk) # FIXME: Is hidden?
        request.user.pinned_posts.add(instance)

        return Response()

    @detail_route(methods=['put'])
    def unpin(self, request, pk=None):
        """
        Removes post from user pinned posts list
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        if self.request.user.is_anonymous():
            return self.permission_denied(request)
        instance = get_object_or_404(Post, pk=pk)
        request.user.pinned_posts.remove(instance)

        return Response()


class PinnedPostsViewSet(mixins.ListModelMixin,
                         viewsets.GenericViewSet):

    serializer_class = PostPublicSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.pinned_posts.all()  # FIXME (VM): What about hidden posts?

    def list(self, request, *args, **kwargs):
        """
        Returns list of posts without hidden posts.
        ---
        parameters:
            - name: user
              description: filter result by user id
              paramType: query
              type: int
        """
        # return Response(self._list(request, self.get_queryset(),
        #                            self.get_serializer, fill_posts))
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = fill_posts(serializer.data, request.user, request)
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = fill_posts([serializer.data], request.user, request)

        return Response(data)


class VotedPostBaseView(mixins.ListModelMixin,
                        viewsets.GenericViewSet):

    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = PostPublicSerializer

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        if page is not None:
            # Get list of identifiers of voted posts
            ids = [it.post_id for it in page]
            posts = Post.objects.filter(id__in=ids)

            serializer = self.get_serializer(posts, many=True)
            posts = fill_posts(serializer.data, request.user, request)

            return self.get_paginated_response(posts)
        else:
            return Response()


# TODO: Add tests?
class VotedPostsViewSet(VotedPostBaseView):
    def get_queryset(self):
        return PostVote.objects.filter(user=self.request.user, is_positive=True)


# TODO: Add tests?
class DonwvotedPostsViewSet(VotedPostBaseView):
    def get_queryset(self):
        return PostVote.objects.filter(user=self.request.user, is_positive=False)


# TODO (VM): Check if post is hidden
class CommentsViewSet(PerObjectPermissionMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = PostComment.objects.all()
    public_serializer_class = CommentPublicSerializer
    private_serializer_class = CommentSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)

    def create(self, request, *args, **kwargs):
        """
        Creates new comment

        parameters:
            - name: post
              description: comment post id
        """
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """

        ---
        parameters:
            - name: user
              description: filter result by user id
              paramType: query
              type: int
        """
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Deletes user comment
        ---
        omit_serializer: true
        parameters:
            - name: pk
              description: comment id
        """
        return super().destroy(request, *args, **kwargs)
