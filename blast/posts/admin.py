from django.contrib import admin

from posts.models import Post, PostComment, PostVote, PostReport, Tag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'text', 'image', 'video', 'time_remains', 'created_at')


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'post', 'text', 'created_at')


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'is_positive', 'created_at')


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'reason', 'text', 'created_at')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('title', 'total_posts')
    readonly_fields = ('title', 'total_posts')
