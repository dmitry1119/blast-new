from rest_framework.response import Response
from rest_framework import status, viewsets, mixins, permissions

from users.serializers import RegisterUserSerializer, PublicUserSerializer, UpdateUserSerializer
from users.models import User
from users.signals import user_registered


class UserViewSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.filter(is_private=False)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return PublicUserSerializer

        if self.request.method == 'POST':
            return RegisterUserSerializer

        if self.request.metoh == 'PATCH':
            return UpdateUserSerializer

    def create(self, request, *args, **kwargs):
        """
        Register user by phone, username, password and avatar.
        """
        serializer = self.get_serializer_class()
        serializer = serializer(data=self.request.data)

        if serializer.is_valid():
            user = serializer.save()

            data = {
                'message': 'register completed successfully',
                'user_id': user.id
            }

            user_registered.send(sender=user)

            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                'message': 'registration failed',
                'errors': serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        return Response(data={'message': 'not implemented'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)
