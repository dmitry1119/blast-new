from rest_framework import viewsets, permissions, mixins, generics

from notifications.models import Notification, FollowRequest
from notifications.serializers import NotificationPublicSerializer, FollowRequestPublicSerializer, \
    FollowRequestSerializer


class NotificationsViewSet(viewsets.ReadOnlyModelViewSet):

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
