from django.contrib import admin

from reports.models import Report


@admin.register(Report)
class ReportsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'reason', 'content_type', 'object_pk', 'content_object', 'user')
