from django.contrib import admin
from notifications.models import Notification, FollowRequest


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text', 'created_at')


@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followee', 'created_at')