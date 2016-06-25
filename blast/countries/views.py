
from rest_framework import viewsets, mixins
from countries.models import Country
from countries.serializers import CountrySerializer


class CountryViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()
