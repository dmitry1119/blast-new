from django.contrib import admin

from tags.models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('title', 'total_posts')
    readonly_fields = ('title', 'total_posts')
    search_fields = ('title',)