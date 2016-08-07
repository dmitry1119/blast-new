from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets

from tags.models import Tag


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    search_fields = ('title',)



# class TagsSearchViewSet(generics.ListAPIView,
#                         generics.GenericAPIView):
#     serializer_class = TagPublicSerializer