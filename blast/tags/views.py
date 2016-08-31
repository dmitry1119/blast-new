from django.shortcuts import render, get_object_or_404

# Create your views here.
from rest_framework import viewsets, filters, generics, permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from posts.models import Post
from core.views import ExtandableModelMixin
from tags.models import Tag
from tags.serializers import TagPublicSerializer


# On each tab it's populated by popularity/randomness so on the users tab for every 10 displayed 7
# are most popular and 3 are random.
# On tags tab the ones pinned will appear at the top then underneath ones that is most popular
# (has the most posts with the tag)
class TagsViewSet(ExtandableModelMixin,
                  viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('-total_posts')
    serializer_class = TagPublicSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('title',)

    permission_classes = (permissions.IsAuthenticated,)

    @detail_route(['put'])
    def pin(self, request, pk=None):
        tag = get_object_or_404(Tag, title=pk)

        if not request.user.pinned_tags.filter(title=tag).exists():
            request.user.pinned_tags.add(tag)

        return Response()

    @detail_route(['put'])
    def unpin(self, request, pk=None):
        if request.user.pinned_tags.filter(title=pk).exists():
            tag = get_object_or_404(Tag, title=pk)
            request.user.pinned_tags.remove(tag)

        return Response()


class TagViewSet(ExtandableModelMixin,
                 viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('-total_posts')
    serializer_class = TagPublicSerializer