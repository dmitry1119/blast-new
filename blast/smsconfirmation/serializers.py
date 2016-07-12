from rest_framework import serializers

from smsconfirmation.models import PhoneConfirmation
from users.models import User


class SinchVerificationSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=10)
    event = serializers.CharField(max_length=25)
    method = serializers.CharField(max_length=10)
    status = serializers.CharField(max_length=15)
    reason = serializers.CharField(max_length=50)


class SinchPhoneConfirmationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=4,
                                 min_length=4)


class PhoneConfirmationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneConfirmation
        fields = ('phone',)


class RequestChangePasswordSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError({'phone': ['Phone does not exist']})

        return value

    class Meta:
        model = PhoneConfirmation
        fields = ('phone',)


class ChangePasswordSerializer(serializers.ModelSerializer):
    """Serializer for unauthorized user"""
    password1 = serializers.CharField(min_length=6)
    password2 = serializers.CharField(min_length=6)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError('Passwords do not match')
        return data

    class Meta:
        model = PhoneConfirmation
        fields = ('phone', 'code', 'password1', 'password2')