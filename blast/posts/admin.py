from django.contrib import admin

from posts.models import Post, PostComment, PostVote, PostReport
from users.models import PinnedPosts
from django.db import models
from django import forms


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'text', 'image', 'video', 'time_remains', 'created_at')
    readonly_fields = ('voted_count', 'downvoted_count',)

    formfield_overrides = {
        models.DateTimeField: {'widget': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S.%f')},
    }

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'post', 'text', 'created_at')


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'is_positive', 'created_at')


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'reason', 'text', 'created_at')


@admin.register(PinnedPosts)
class PinnedPostsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post_id', 'user_id',)
