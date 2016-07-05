from rest_framework import viewsets, mixins, permissions, generics

from users.models import User, UserSettings
from users.serializers import (RegisterUserSerializer, PublicUserSerializer,
                               ProfilePublicSerializer, ProfileUserSerializer,
                               NotificationSettingsSerializer)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return PublicUserSerializer
        else:
            return RegisterUserSerializer

    def create(self, request, *args, **kwarg):
        """
        Register user by phone, username, password, country id and confirmation code received by sms.
        Avatar field is optional and can be set after registration.

        ---
        parameters:
            - name: code
              description: code received by sms.
            - name: phone
              description: user phone number with country code (e.g. +79131234567, +1-492-9131234567)
            - name: username
              description: unique user name. Must be less then 16 symbols.
            - name: password
              description: user password. Must be greater than 5 symbols.
            - name: country
              description: user country id.
        """
        return super().create(request, *args, **kwarg)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """

    ---
    PATCH:
        parameters:
            - name: website
              description: user website
            - name: gender
              description: 0 - female, 1 - male.
    PUT:
        parameters:
            - name: website
              description: user website
            - name: gender
              description: 0 - female, 1 - male.
    """
    queryset = User.objects.all()

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfilePublicSerializer

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ProfilePublicSerializer
        else:
            return ProfileUserSerializer

    def get_object(self):
        self.request.user.refresh_from_db()
        return self.request.user


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """

    ---
    PATCH:
        parameters:
            - name: notify_comments
              description: 0 - off, 1 - people I follow, 2 - everyone.
            - name: notify_reblasts
              description: 0 - off, 1 - people I follow, 2 - everyone.
    PUT:
        parameters:
            - name: notify_comments
              description: 0 - off, 1 - people I follow, 2 - everyone.
            - name: notify_reblasts
              description: 0 - off, 1 - people I follow, 2 - everyone.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSettingsSerializer

    def get_object(self):
        instance, _ = UserSettings.objects.get_or_create(user=self.request.user)
        return instance

