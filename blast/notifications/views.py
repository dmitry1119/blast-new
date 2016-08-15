from rest_framework import viewsets, permissions

from notifications.models import Notification
from notifications.serializers import NotificationPublicSerializer


class NotificationsViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationPublicSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)