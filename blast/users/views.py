from rest_framework import viewsets, mixins, permissions, generics
from rest_framework.decorators import list_route
from rest_framework.response import Response

from users.models import User, UserSettings
from users.serializers import (RegisterUserSerializer, PublicUserSerializer,
                               ProfilePublicSerializer, ProfileUserSerializer,
                               NotificationSettingsSerializer, ChangePasswordSerializer, ChangePhoneSerializer,
                               ChangePhoneRequestSerializer, CheckUsernameAndPassword)


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
        Register user by phone, username, password, avatar, country id and confirmation code received by sms.

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

    @list_route(['get'])
    def check(self, request, *args, **kwargs):
        serializer = CheckUsernameAndPassword(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return Response()


class UserProfileView(generics.RetrieveUpdateAPIView):
    """

    ---
    PATCH:
        parameters:
            - name: website
              description: user website
            - name: gender
              description: 0 - female, 1 - male.
            - name: avatar
              required: false
              type: file
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


class UserPasswordResetView(generics.UpdateAPIView):
    """
    Changes password for authorized user

    ---
    PUT:
        - name: old_password
          description: old user password
        - name: password1
          description: new password
        - name: password2
          description: new password confirmation
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user


class UserChangePhoneView(generics.UpdateAPIView,
                          generics.CreateAPIView):
    """
    Changes user phone

    ---
    PUT:
        - name: password
          description: user password
        - name: old_phone
          description: old user phone
        - name: new_phone
          description: new user phone
        - name: code
          description: code received by sms
    """
    permissions_class = (permissions.IsAuthenticated,)
    serializer_class = ChangePhoneSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChangePhoneRequestSerializer
        elif self.request.method == 'PATCH':
            return ChangePhoneSerializer

    def get_object(self):
        return self.request.user

    def post(self, *args, **kwargs):
        """
        Requests new confirmation for phone changing

        ---
        parameters:
            - name: phone
              description: new user phone

        """
        return super().post(*args, **kwargs)
