from rest_framework import viewsets, mixins, permissions

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
    queryset = Post.objects.all()  # FIXME(VM): What about private users?
    serializer_class = PostSerializer

    public_serializer_class = PostPublicSerializer
    private_serializer_class = PostSerializer

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


class CommentsViewSet(PerObjectPermissionMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = PostComment.objects.all()
    public_serializer_class = CommentPublicSerializer
    private_serializer_class = CommentSerializer

    def create(self, request, *args, **kwargs):
        """
        Creates new comment

        parameters:
            - name: post
              description: commented post id
        """
        return super().create(request, *args, **kwargs)

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


class VotePostView(PerObjectPermissionMixin,
                   mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.ViewSet):

    queryset = PostVote.objects.all()

    public_serializer_class = PostSerializer
    private_serializer_class = PostPublicSerializer

    def get_object(self):
        if self.request.method in permissions.SAFE_METHODS:
            return super(viewsets.ViewSet, self).get_object()
        else:
            return PostVote.objects.get_or_create(user=self.request.user, is_voted=True)