from django.contrib import admin

from posts.models import Post, PostComment, PostVote, PostReport


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'text', 'image', 'video', 'time_remains', 'created_at')


@admin.register(PostComment)
class PostComment(admin.ModelAdmin):
    list_display = ('pk', 'user', 'post', 'text', 'created_at')


@admin.register(PostVote)
class PostVote(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'is_positive', 'created_at')


@admin.register(PostReport)
class PostReport(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'reason', 'text', 'created_at')