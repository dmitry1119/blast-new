from rest_framework import serializers

from tags.models import Tag


class TagPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'