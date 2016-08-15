from rest_framework import serializers

from notifications.models import Notification


class NotificationPublicSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    # FIXME: Can be expensive
    def get_user(self, obj):
        if not obj.other:
            return None

        request = self.context['request']
        data = {
            'id': obj.other.pk,
            'username': obj.other.username,
            'avatar': None
        }

        if obj.other.avatar:
            data['avatar'] = request.build_absolute_uri(obj.other.avatar.url)

        return data

    class Meta:
        model = Notification
        exclude = ('user', 'other')
