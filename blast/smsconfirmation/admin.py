from django.contrib import admin

from smsconfirmation.models import PhoneConfirmation

@admin.register(PhoneConfirmation)
class PhoneConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'updated_at',
                    'is_delivered', 'is_confirmed')

    class Meta:
        model = PhoneConfirmation
