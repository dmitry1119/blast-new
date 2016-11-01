from django.contrib import admin
from notifications.models import Notification, FollowRequest

from notifications.tasks import send_push_notification


def resend(modeladmin, request, qs):
    for it in qs:
        send_push_notification.delay(it.user_id, it.text, it.push_payload)

resend.short_description = 'Send push notifications'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text', 'type', 'created_at')
    actions = [resend]


@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followee', 'created_at')