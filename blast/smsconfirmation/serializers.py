from rest_framework import serializers

from smsconfirmation.models import PhoneConfirmation
from users.models import User


class PhoneConfirmationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneConfirmation
        fields = ('phone',)


class RequestChangePasswordSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Phone does not exist')

        return value

    class Meta:
        model = PhoneConfirmation
        fields = ('phone',)


class RequestChangePasswordSerializerUnauth(serializers.ModelSerializer):
    username = serializers.CharField(max_length=15, write_only=True)

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username does not exist')

        return value

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Phone does not exist')

        return value

    def validate(self, data):
        super().validate(data)
        del data['username']

        return data

    class Meta:
        model = PhoneConfirmation
        fields = ('phone', 'username')


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