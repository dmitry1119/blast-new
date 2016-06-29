from rest_framework import views, viewsets, mixins, permissions, status
from rest_framework.response import Response

from posts.models import Post, PostComment
from posts.serializers import PostSerializer, PostPublicSerializer


class PostsViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    queryset = Post.objects.all()  # FIXME: What about private users?
    serializer_class = PostSerializer

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return PostPublicSerializer
        else:
            return PostSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return permissions.AllowAny(),
        else:
            return permissions.IsAuthenticated(),

    def check_object_permissions(self, request, obj: Post):
        if request.method in permissions.SAFE_METHODS:
            return

        if obj.user is not request.user:
            return self.permission_denied(self.request, 'You are not owner of this post')

    def create(self, request, *args, **kwargs):
        """Creates new blast"""
        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            return Response(data={
                'message': 'Failed to create post',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)