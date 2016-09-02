import logging

from django.shortcuts import render, get_object_or_404
import redis

from posts.serializers import PostPublicSerializer

# Create your views here.
from rest_framework import viewsets, filters, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from posts.models import Post
from core.views import ExtendableModelMixin
from tags.models import Tag
from tags.serializers import TagPublicSerializer


logger = logging.Logger(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


def extend_tags(data, serializer_context):
    tags = {it['title'] for it in data}

    # Attaches posts to tags
    posts = []
    tags_to_posts = {}
    for tag in tags:
        key = Tag.redis_posts_key(tag)
        tag_post_ids = r.zrevrange(key, 0, 5)  # This defines order of posts. See zrevrange doc.
        tag_post_ids = [int(i) for i in tag_post_ids]

        tags_to_posts[tag] = tag_post_ids
        posts.extend(tag_post_ids)

    # Pulls posts from db and builds in-memory index
    posts = Post.objects.filter(pk__in=posts)
    posts = {it.pk: it for it in posts}

    for it in data:
        tag_post_ids = tags_to_posts[it['title']]
        tag_posts = []
        for post_id in tag_post_ids:
            if post_id in posts:
                tag_posts.append(posts[post_id])

            if len(tag_posts) >= 3:  # FIXME (VM): Magic number?
                break

        # Order of posts is defined by zrevrange
        serializer = PostPublicSerializer(tag_posts, many=True, context=serializer_context)
        it['posts'] = serializer.data

    return data


# On each tab it's populated by popularity/randomness so on the users
# tab for every 10 displayed 7 are most popular and 3 are random.
# On tags tab the ones pinned will appear at the top then underneath ones that is most popular
# (has the most posts with the tag)
class TagsViewSet(ExtendableModelMixin,
                  viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('-total_posts')
    serializer_class = TagPublicSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('title',)

    permission_classes = (permissions.IsAuthenticated,)

    def extend_response_data(self, data):
        serializer_context = self.get_serializer_context()
        extend_tags(data, serializer_context)
        if not self.request.user.is_authenticated():
            return

        tags = {it['title'] for it in data}
        pinned = self.request.user.pinned_tags.filter(title__in=tags)
        pinned = pinned.values('title')
        pinned = {it['title'] for it in pinned}

        for it in data:
            it['is_pinned'] = it['title'] in pinned

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

    @list_route(['get'])
    def pinned(self, request):
        qs = request.user.pinned_tags.all()
        page = self.paginate_queryset(qs)

        serializer_context = self.get_serializer_context()
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            for it in response.data['results']:
                it['is_pinned'] = True

            extend_tags(response.data['results'], serializer_context)

            return response

        serializer = self.get_serializer(qs, many=True)
        extend_tags(serializer.data, serializer_context)

        for it in serializer.data['results']:
            it['is_pinned'] = True
        return Response(serializer.data)


class TagViewSet(ExtendableModelMixin,
                 viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('-total_posts')
    serializer_class = TagPublicSerializer