from rest_framework import serializers

from smsconfirmation.models import PhoneConfirmation


class PhoneConfirmationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneConfirmation
        fields = ('phone',)


class RequestChangePasswordSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneConfirmation
        fields = ('phone',)


class ChangePasswordSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(min_length=6)
    password2 = serializers.CharField(min_length=6)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError('Passwords do not match')

        return data

    class Meta:
        model = PhoneConfirmation
        fields = ('phone', 'code', 'password1', 'password2')