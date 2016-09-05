import logging

import itertools
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
        tag_post_ids = Tag.get_posts(tag, 0, 5)

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
    def unpinned(self, request):
        if not self.request.user.is_authenticated():
            return self.queryset

        page = request.query_params.get('page', 0)
        page_size = request.query_params.get('page_size', 50)

        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            logging.error('Failed to cast page and page size to int')
            return Response('page and page_size should be int', status=400)

        start = page * page_size
        end = (page + 1) * page_size

        pinned = self.request.user.pinned_tags.all()
        pinned_tags = {it.title for it in pinned}

        qs = Tag.objects.exclude(title__in=pinned_tags)
        tags = qs[start:end]

        context = self.get_serializer_context()
        serializer = TagPublicSerializer(tags, many=True, context=context)
        for it in serializer.data:
            it['is_pinned'] = False

        return Response({
            'count': qs.count(),
            'results': serializer.data
        })

    @list_route(['get'])
    def pinned(self, request):
        qs = request.user.pinned_tags.all()
        page = self.paginate_queryset(qs)

        serializer_context = self.get_serializer_context()
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            for it in serializer.data:
                it['is_pinned'] = True

            extend_tags(response.data['results'], serializer_context)

            return response

        serializer = self.get_serializer(qs, many=True)
        for it in serializer.data:
            it['is_pinned'] = True

        extend_tags(serializer.data, serializer_context)

        return Response(serializer.data)

    @list_route(['get'])
    def feeds(self, request):
        page = self.request.query_params.get('page', 0)
        page_size = self.request.query_params.get('page_size', 50)

        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            return Response('page and page_size should be int', status=400)

        start = page * page_size
        end = (page + 1) * page_size

        pinned_qs = self.request.user.pinned_tags.all()
        pinned_count = pinned_qs.count()
        pinned = []

        rest_qs = Tag.objects.all().order_by('-total_posts')
        rest_count = rest_qs.count()
        rest = []

        print(start, end, page_size, pinned_count, start <= pinned_count and pinned_count <= end)
        if start < pinned_count and pinned_count <= end:  # Case 2
            pinned = pinned_qs[start:pinned_count]
            pinned_tags = {it.title for it in pinned}

            rest_qs = rest_qs.exclude(title__in=pinned_tags)
            r_start = max(0, start - pinned_count)
            r_end = end - pinned_count

            rest = rest_qs[r_start:r_end]
        elif end < pinned_count:  # Case 2
            pinned = pinned_qs[start:end]
        elif start >= pinned_count:  # Case 3
            r_start = max(0, start - pinned_count)
            r_end = end - pinned_count

            pinned_tags = {it.title for it in pinned_qs.all()}
            rest = rest_qs.exclude(title__in=pinned_tags)[r_start:r_end]

        context = self.get_serializer_context()

        pinned = TagPublicSerializer(pinned, many=True, context=context).data
        for it in pinned:
            it['is_pinned'] = True

        rest = TagPublicSerializer(rest, many=True, context=context).data
        for it in rest:
            it['is_pinned'] = False

        results = itertools.chain(pinned, rest)

        return Response({
            'count': rest_count + pinned_count,
            'results': results
        })


class TagExactSearchView(viewsets.ReadOnlyModelViewSet):
    """Returns list of post for given tag

    ---
    list:
        parameters:
            - name: search
              type: string
              description: tag name to search
            - name: order
              type: string
              description: Should be 'newest' or 'featured'
    """

    serializer_class = PostPublicSerializer

    def get_queryset(self):
        tag = self.request.query_params.get('search')
        qs = Post.objects.actual().filter(tags=tag)

        order = self.request.query_params.get('order', 'neweset')
        if order == 'newest':
            qs = qs.order_by('created_at')
        else:
            qs = qs.order_by('-created_at')

        return qs


class TagViewSet(ExtendableModelMixin,
                 viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('-total_posts')
    serializer_class = TagPublicSerializer