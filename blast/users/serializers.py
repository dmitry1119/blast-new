from rest_framework import serializers

from smsconfirmation.models import CODE_CONFIRMATION_LEN, PhoneConfirmation
from users.models import User, UserSettings


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Serializer for registration method.
    It allows set up very limited field set.
    """
    code = serializers.CharField(max_length=CODE_CONFIRMATION_LEN,
                                 min_length=CODE_CONFIRMATION_LEN,
                                 write_only=True)

    def validate_password(self, value):
        if not value or len(value) < 6:
            raise serializers.ValidationError('Your password must be at least 6 characters')
        return value

    def validate_username(self, value):
        if not value or len(value) > 15:
            raise serializers.ValidationError('Your username must be 15 characters or less')
        return value

    def create(self, validated_data):
        confirmation = PhoneConfirmation.objects.get_actual(validated_data['phone'],
                                                            request_type=PhoneConfirmation.REQUEST_PHONE)

        if not confirmation:
            raise serializers.ValidationError('Confirmation code was not found')

        if not confirmation.is_actual():
            raise serializers.ValidationError('You phone code is expired')

        if confirmation.code != validated_data['code']:
            raise serializers.ValidationError('Wrong confirmation code')

        instance = User.objects.create_user(phone=validated_data['phone'],
                                            password=validated_data['password'],
                                            username=validated_data['username'],
                                            country=validated_data['country'])
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('phone', 'username', 'password', 'avatar', 'country', 'code')


class ProfileUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user model
    """
    class Meta:
        model = User
        fields = ('fullname', 'avatar', 'bio', 'website', 'gender', 'birthday',)


class ProfilePublicSerializer(serializers.ModelSerializer):
    """
    Special serializer for logged user
    """
    followers = serializers.ReadOnlyField(source='followers_count')
    blasts = serializers.ReadOnlyField(source='blasts_count')
    following = serializers.ReadOnlyField(source='following_count')

    class Meta:
        model = User
        exclude = ('password', 'user_permissions', 'groups',)


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
        fields = ('id', 'username', 'created_at', 'fullname', 'avatar',
                  'bio', 'website', 'followers', 'blasts', 'following')


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        exclude = ('user',)