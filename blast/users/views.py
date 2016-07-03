from django.http import Http404
from rest_framework.response import Response
from rest_framework import status, views, viewsets, mixins, permissions

from users.serializers import (RegisterUserSerializer, PublicUserSerializer, UpdateUserSerializer,
                               NotificationSettingsSerializer)

from users.models import User, UserSettings
from users.signals import user_registered


class UserViewSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS or self.request.method == 'POST':
            return (permissions.AllowAny(),)
        else:
            return (permissions.IsAuthenticated(),)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return PublicUserSerializer
        elif self.request.method == 'POST' or self.request.method == 'PUT':
            return RegisterUserSerializer
        elif self.request.method == 'PATCH':
            return UpdateUserSerializer

    def create(self, request, *args, **kwargs):
        """
        Register user by phone, username, password and country id.
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
            - name: user country identifier.
        """
        return super().create(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object()

        if self.request.method in permissions.SAFE_METHODS:
            return obj
        elif obj != self.request.user:
            raise Http404()

        return obj

    def update(self, request, *args, **kwargs):
        """
        Updates user profile

        ---
        parameters:
            - name: fullname
              description: user fullname
            - name: avatar
              description: user avatar image.
            - name: gender
              description: user gender. 0 for female and 1 for male.
            - name: user country identifier.
        """
        return super().update(request, *args, **kwargs)


class UserSettingsViewSet(mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin,
                          views.APIView):

    # TODO: Make permissions test
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        instance, _ = UserSettings.objects.get_or_create(user=self.request.user)
        return instance

    def get_serializer_class(self):
        return NotificationSettingsSerializer

    # TODO: Make permissions test
    def get(self, request, *args, **kwargs):
        """Returns user settings"""
        instance = self.get_object()
        serializer = self.get_serializer_class()(instance=instance)

        return Response(serializer.data)

    # TODO: Make permissions test
    def patch(self, request, *args, **kwargs):
        """Updates user settings"""
        instance = self.get_object()

        serializer = self.get_serializer_class()
        serializer = serializer(instance=instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(data={'message': 'ok'})
        else:
            return Response(data={
                'message': 'failed to update user settings',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)