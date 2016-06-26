from rest_framework import serializers

from smsconfirmation.models import PhoneConfirmation

class PhoneConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneConfirmation
        fields = ('code',)