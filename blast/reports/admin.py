from datetime import timedelta

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from push_notifications.models import APNSDevice

from notifications.models import Notification
from posts.models import Post
from reports.models import Report


def mark_for_removal(modeladmin, request, qs):
    content_type = ContentType.objects.get(app_label='posts', model='post')

    # Pull posts from reports
    reports = list(qs.filter(content_type=content_type).values('user_id', 'object_pk'))

    expired_at = timezone.now() + timedelta(minutes=10)

    # Mark post for removal
    post_ids = {it['object_pk'] for it in reports}
    Post.objects.filter(pk__in=post_ids).update(expired_at=expired_at, is_marked_for_removal=True)

    # Send notification PUSH'es
    # for it in reports:
    #     Notification.objects.create()


mark_for_removal.short_description = 'Mark for removal (posts only)'


@admin.register(Report)
class ReportsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'reason', 'content_type', 'object_pk', 'content_object', 'user')
    actions = [mark_for_removal]