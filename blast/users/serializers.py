from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.models import User


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Serializer for registration method.
    It allows set up very limited field set.
    """

    def validate_password(self, value):
        if not value or len(value) < 6:
            raise serializers.ValidationError('Your password must be at least 6 characters')
        return value

    def validate_username(self, value):
        if not value or len(value) > 15:
            raise serializers.ValidationError('Your username must be 15 characters or less')
        return value

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('phone', 'username', 'password', 'avatar', 'country')


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user model
    """

    class Meta:
        model = User
        fields = ('fullname', 'avatar', 'bio', 'website', 'gender', 'birthday',)


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Serializer for safe methods.
    It serialize only safe public methods, like username, avatar etc.
    """
    followers = serializers.ReadOnlyField(source='followers_count')
    blasts = serializers.ReadOnlyField(source='blasts_count')
    following = serializers.ReadOnlyField(source='following_count')

    class Meta:
        model = User
        fields = ('id', 'username', 'created_at', 'birthday', 'fullname', 'avatar',
                  'bio', 'website', 'followers', 'blasts', 'following')