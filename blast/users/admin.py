from django.contrib import admin
from users.models import User, UserSettings, Follower, BlockedUsers


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'phone',)
    search_fields = ('phone',)


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'followee', 'follower', 'created_at')


@admin.register(BlockedUsers)
class BlockedUsersAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'blocked', 'created_at',)