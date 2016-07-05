from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from posts.models import Post, PostComment, PostVote
from posts.serializers import (PostSerializer, PostPublicSerializer,
                               CommentSerializer, CommentPublicSerializer,
                               VoteSerializer, VotePublicSerializer)


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


class PostsViewSet(PerObjectPermissionMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    queryset = Post.objects.filter(is_hidden=False)  # FIXME(VM): What about private users?
    serializer_class = PostSerializer

    public_serializer_class = PostPublicSerializer
    private_serializer_class = PostSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)

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
        return super().list(request, *args, **kwargs)

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

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

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
        responseMessages:
            - code: 201 if vote does not exist
            - code: 200 it vote updated
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
        responseMessages:
            - code: 201 if vote does not exist
            - code: 200 it vote updated
        """
        return self._update_vote(request, False, pk)

    def _update_visibility(self, pk, is_hidden):
        post = get_object_or_404(Post, pk=pk)
        if post.user != self.request.user:
            self.permission_denied(self.request, 'You are not owner of this object')

        post.is_hidden = is_hidden
        post.save()

        return Response()

    @detail_route(methods=['patch'])
    def hide(self, request, pk=None):
        """
        Hide post

        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        return self._update_visibility(pk, True)

    @detail_route(methods=['patch'])
    def show(self, request, pk=None):
        """
        Show post

        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        """
        return self._update_visibility(pk, False)


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
