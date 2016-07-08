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
            raise serializers.ValidationError({'code': ['Confirmation code was not found']})

        if not confirmation.is_actual():
            raise serializers.ValidationError({'code': ['You phone code is expired']})

        if confirmation.code != validated_data['code']:
            raise serializers.ValidationError({'code': ['Wrong confirmation code']})

        instance = User.objects.create_user(phone=validated_data['phone'],
                                            password=validated_data['password'],
                                            username=validated_data['username'],
                                            country=validated_data['country'])
        instance.set_password(validated_data['password'])

        avatar = validated_data.get('avatar')
        if avatar:
            instance.avatar.save(avatar.name, avatar)

        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('phone', 'username', 'password', 'country', 'avatar', 'code')


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
    followers = serializers.ReadOnlyField(source='followers_count',
                                          help_text='Total count of followers')
    blasts = serializers.ReadOnlyField(source='blasts_count',
                                       help_text='Total count of blasts')
    following = serializers.ReadOnlyField(source='following_count',
                                          help_text='Total count of followee')

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


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(min_length=6, write_only=True)
    password1 = serializers.CharField(min_length=6, write_only=True)
    password2 = serializers.CharField(min_length=6, write_only=True)

    def validate_old_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError({'old_password': 'Wrong old password'})

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'password1': ['Passwords do not match']})

        return data

    def save(self, **kwargs):
        self.instance.set_password(self.validated_data['password1'])
        super().save(**kwargs)

    class Meta:
        model = User
        fields = ('password1', 'password2', 'old_password')


class ChangePhoneSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=6, write_only=True)
    current_phone = serializers.CharField(write_only=True)
    new_phone = serializers.CharField(write_only=True)

    def validate_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError({'password': 'Wrong password'})

        return value

    def validate_current_phone(self, value):
        if self.instance.phone != value:
            raise serializers.ValidationError({'current_phone': 'Wrong current phone number'})

        return value

    def save(self, **kwargs):
        self.instance.phone = self.validated_data['new_phone']
        super().save(**kwargs)

    class Meta:
        model = User
        fields = ('password', 'current_phone', 'new_phone',)