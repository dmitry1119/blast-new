from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import filters
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from core.views import ExtandableModelMixin

from posts.models import Post, PostComment, PostVote
from posts.serializers import (PostSerializer, PostPublicSerializer,
                               CommentSerializer, CommentPublicSerializer,
                               VoteSerializer, ReportPostSerializer)

from datetime import timedelta, datetime


from tags.models import Tag
from users.models import User, Follower, BlockedUsers

from users.serializers import UsernameSerializer


# FIXME: Replace by custom permission class
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


# TODO: Add feeds test, check author, hidden posts and voted posts
class FeedsView(ExtandableModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.filter(Q(user__is_private=False) | Q(user=None),
                                   expired_at__gte=timezone.now())

    serializer_class = PostPublicSerializer

    def extend_response_data(self, data):
        fill_posts(data, self.request.user, self.request)

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user

        if not user.is_authenticated():
            return qs

        # Add followers posts
        # FIXME (VM): cache list in redis?
        followees = Follower.objects.filter(follower=self.request.user)
        followees = {it.followee_id for it in followees}
        qs = qs.filter(user__in=followees)

        # Exclude blocked users
        # FIXME (VM): cache list in redis?
        blocked = BlockedUsers.objects.filter(user=self.request.user)
        blocked = {it.blocked_id for it in blocked}
        qs = qs.filter(user__in=blocked)

        # Excludes hidden posts
        # FIXME (VM): cache list in redis?
        hidden = user.hidden_posts.all().values('pk')
        hidden = {it['pk'] for it in hidden}
        qs = qs.exclude(pk__in=hidden)

        # Exclude voted posts
        # FIXME (VM): votes list can be very large
        # FIXME (VM): cache list in redis?
        voted = PostVote.objects.filter(user=user.pk).values('post')
        voted = {it['post'] for it in voted}
        qs = qs.exclude(pk__in=voted)

        return qs


class PostsViewSet(PerObjectPermissionMixin,
                   ExtandableModelMixin,
                   viewsets.ModelViewSet):
    """
    ---
    create:
        parameters:
            - name: video
              type: file
            - name: image
              type: file
    """
    queryset = Post.objects.public()

    public_serializer_class = PostPublicSerializer
    private_serializer_class = PostSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user', 'tags', 'is_anonymous')

    def extend_response_data(self, data):
        fill_posts(data, self.request.user, self.request)

    # TODO: Move to mixin
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Changes response use PostPublicSerializer
        data = PostPublicSerializer(serializer.instance, context=self.get_serializer_context()).data
        data = fill_posts([data], request.user, request)
        return Response(data[0], status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        post = serializer.instance
        if post.is_anonymous:
            self.request.user.pinned_posts.add(post)

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

        if is_positive:
            post.expired_at += timedelta(minutes=5)
            post.save()
        else:
            post.expired_at -= timedelta(minutes=10)
            post.save()

        vote.save()
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

    @detail_route(methods=['get'])
    def voters(self, request, pk=None):
        qs = PostVote.objects.filter(post=pk, is_positive=True)\
            .prefetch_related('user')

        page = self.paginate_queryset(qs)

        users = [it.user for it in page]

        serializer = UsernameSerializer(users, many=True,
                                        context=self.get_serializer_context())

        if request.user.is_authenticated():
            followees = Follower.objects.filter(followee__in=users,
                                                follower=request.user)
            followees = followees.prefetch_related('followee')
            followees = {it.followee.pk for it in followees}
            for it in serializer.data:
                it['is_followee'] = it['id'] in followees
        else:
            for it in serializer.data:
                it['is_followee'] = False

        return self.get_paginated_response(serializer.data)

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
        instance = get_object_or_404(Post, pk=pk)
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


class PinnedPostsViewSet(ExtandableModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = PostPublicSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def extend_response_data(self, data):
        fill_posts(data, self.request.user, self.request)    

    def get_queryset(self):
        return self.request.user.pinned_posts.filter(expired_at__gte=timezone.now()).all()


class VotedPostBaseView(mixins.ListModelMixin,
                        viewsets.GenericViewSet):

    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = PostPublicSerializer

    # TODO: Exclude hidden posts
    def get_queryset(self):
        # FIXME: This list can be big.
        voted_ids = PostVote.objects.filter(user=self.request.user,
                                            is_positive=self.is_positive)
        voted_ids = [it.post_id for it in voted_ids]
        return Post.objects.filter(pk__in=voted_ids, 
                                   expired_at__gte=timezone.now())

    def list(self, request, *args, **kwargs):
        response = super().list(self, request, *args, **kwargs)
        fill_posts(response.data['results'], request.user, request)

        return response


class VotedPostsViewSet(VotedPostBaseView):
    is_positive = True


class DonwvotedPostsViewSet(VotedPostBaseView):
    is_positive = False


# TODO (VM): Check if post is hidden
# TODO (VM): Remove Update actions
class CommentsViewSet(PerObjectPermissionMixin,
                      ExtandableModelMixin,
                      viewsets.ModelViewSet):
    queryset = PostComment.objects.all()
    public_serializer_class = CommentPublicSerializer
    private_serializer_class = CommentSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user', 'post', 'parent',)

    def extend_response_data(self, data):
        attach_users(data, self.request.user, self.request)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Changes response use PostPublicSerializer
        data = self.public_serializer_class(serializer.instance).data
        data = attach_users([data], request.user, request)
        return Response(data[0], status=status.HTTP_201_CREATED, headers=headers)

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


class PostSearchViewSet(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = PostPublicSerializer

    queryset = Post.objects.all()

    def get_queryset(self):
        tag = self.request.query_params.get('tag', '')
        tags = Tag.objects.filter(title__istartswith=tag)
        tags = tags.order_by('-total_posts')[:100]

        # Select first 100 posts assume that search output will be short
        pinned = self.request.user.pinned_posts
        pinned = pinned.filter(tags__in=tags, expired_at__gte=timezone.now())
        pinned = pinned.order_by('-expired_at').distinct()[:100]

        posts = Post.objects.filter(tags__in=tags, expired_at__gte=timezone.now())
        posts = posts.exclude(pk__in={it.pk for it in pinned}).distinct()
        posts = posts.order_by('-expired_at')

        return posts
        # result = chain(pinned, posts)
        #
        # return result