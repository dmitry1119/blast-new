from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters, generics

from tags.models import Tag
from tags.serializers import TagPublicSerializer


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagPublicSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('title',)


class TagsSearchViewSet(generics.ListAPIView,
                        generics.GenericAPIView):
    serializer_class = TagPublicSerializer

    def search(self, query):
        tags = Tag.objects.filter(titile__istratwith=query)

        return tags