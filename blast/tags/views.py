from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters, generics

from tags.models import Tag
from tags.serializers import TagPublicSerializer


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('-total_posts')
    serializer_class = TagPublicSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('title',)