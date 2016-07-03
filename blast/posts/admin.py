from django.contrib import admin

from posts.models import Post, PostComment, PostVote

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'text', 'video',)


@admin.register(PostComment)
class PostComment(admin.ModelAdmin):
    list_display = ('pk', 'user', 'post', 'text')


@admin.register(PostVote)
class PostVote(admin.ModelAdmin):
    list_display = ('pk', 'post', 'user', 'is_positive')