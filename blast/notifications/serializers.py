from rest_framework import serializers

from notifications.models import Notification, FollowRequest
from posts.serializers import PreviewPostSerializer
from users.models import Follower


class NotificationPublicSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    post = PreviewPostSerializer()

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
        exclude = ('user', 'post', 'other')


class FollowRequestPublicSerializer(serializers.ModelSerializer):
    follower = serializers.SerializerMethodField()

    def get_follower(self, obj):
        request = self.context['request']
        data = {
            'id': obj.follower.pk,
            'username': obj.follower.username,
            'avatar': None
        }

        if obj.follower.avatar:
            data['avatar'] = request.build_absolute_uri(obj.follower.avatar.url)

        return data

    class Meta:
        model = FollowRequest
        fields = ('id', 'follower', 'created_at')


class FollowRequestSerializer(serializers.ModelSerializer):
    accept = serializers.BooleanField(required=False)

    def _process_request(self, instance, validated_data):
        if validated_data['accept']:
            Follower.objects.create(followee=instance.followee, follower=instance.follower)
            # instance.followee.followers.add(instance.follower)
            # TODO: raise user_follow signal?

        instance.delete()

        return instance

    def update(self, instance, validated_data):
        return self._process_request(instance, validated_data)

    def create(self, validated_data):
        user = self.required['request'].user
        follow_request = FollowRequest.objects.get(pk=validated_data['id'], followee=user.pk)
        return self._process_request(follow_request, validated_data)

    class Meta:
        model = FollowRequest
        fields = ('accept',)
