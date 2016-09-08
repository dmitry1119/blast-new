from rest_framework import viewsets, permissions, mixins, generics
from notifications.models import Notification, FollowRequest
from core.views import ExtendableModelMixin
from notifications.serializers import NotificationPublicSerializer, FollowRequestPublicSerializer, \
    FollowRequestSerializer

from  users.models import User, Follower


class NotificationsViewSet(ExtendableModelMixin,
                           viewsets.ReadOnlyModelViewSet):
    def extend_response_data(self, data):
        request = self.request

        users = {it['other'] for it in data if it['other']}
        users = User.objects.filter(pk__in=users)
        followees = Follower.objects.filter(followee__in=users, follower_id=request.user.pk)

        users = {it.pk: it for it in users}
        followees = {it.followee_id for it in followees}

        for it in data:
            if not it['other']:
                continue

            pk = it['other']
            user = users[pk]
            it['user'] = {
                'id': user.pk,
                'username': user.username,
                'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
                'is_followee': pk in followees
            }

            del it['other']

        return data

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationPublicSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class FollowRequestViewSet(mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return FollowRequest.objects.filter(followee=self.request.user)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return FollowRequestPublicSerializer
        else:
            return FollowRequestSerializer
