from django.contrib import admin
from users.models import User

@admin.register(User)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'phone',)
    search_fields = ('phone',)
