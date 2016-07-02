# Create your views here.
import logging

from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import mixins, views, viewsets, status
from rest_framework import status, permissions

from smsconfirmation.models import PhoneConfirmation
from smsconfirmation.serializers import PhoneConfirmationSerializer, ChangePasswordSerializer, \
    RequestChangePasswordSerializer
from users.models import User

logger = logging.getLogger(__name__)


class PhoneConfirmBase(mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       views.APIView):
    """
    Base class for requests that can be confirmed by phone.

    serializer_class - class for serializing and validating request data.
    queryset - PhoneConfirmation queryset.
    """
    permission_classes = (permissions.AllowAny,)

    def on_code_confirmed(self, request, confirmation):
        raise NotImplemented()

    def post(self, request, *args, **kwargs):
        return self.create(request)

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response({
                'message': 'wrong data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']

        confirmation = self.queryset.filter(phone=phone)
        confirmation = confirmation.order_by('-created_at').first()

        if not confirmation:
            logger.error('Confirmation request for {} was not found'.format(phone))
            return Response({'message': 'confirmation request was not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if not confirmation.is_actual():
            logger.info('Confirmation code is expired {}'.format(confirmation.pk))
            return Response({
                'message': 'Confirmation code is expired'
            }, status=status.HTTP_400_BAD_REQUEST)

        if confirmation.code == serializer.data['code']:
            confirmation.is_confirmed = True
            confirmation.save()

            self.on_code_confirmed(request, confirmation)

            return Response({
                'message': 'ok'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'wrong code'
            }, status=status.HTTP_400_BAD_REQUEST)


class PhoneConfirmView(PhoneConfirmBase):
    serializer_class = PhoneConfirmationSerializer

    # TODO (VM): Add is_delivered to filter?
    queryset = PhoneConfirmation.objects.filter(is_confirmed=False,
                                                request_type=PhoneConfirmation.REQUEST_PHONE)

    def get_serializer(self, data):
        if self.request.method == 'POST':
            return PhoneConfirmationSerializer(data=data)

    def post(self, request, *args, **kwargs):
        """
        Requests new phone confirmation code by SMS.

        ---
        serializer: smsconfirmation.serializers.PhoneConfirmationSerializer
        """
        return super().create(request)

    def perform_create(self, serializer):
        serializer.save(request_type=PhoneConfirmation.REQUEST_PHONE)

    def on_code_confirmed(self, request, confirmation: PhoneConfirmation):
        user = User.objects.get(phone=confirmation.phone)
        user.is_verified = True
        user.save()


# TODO: Fix permissions
class ResetPasswordView(PhoneConfirmBase):

    serializer_class = ChangePasswordSerializer

    # TODO (VM): Add is_delivered to filter?
    queryset = PhoneConfirmation.objects.filter(is_confirmed=False,
                                                request_type=PhoneConfirmation.REQUEST_PASSWORD)

    def get_serializer(self, data):
        if self.request.method == 'POST':
            return RequestChangePasswordSerializer(data=data)
        else:
            return ChangePasswordSerializer(data=data)

    def perform_create(self, serializer):
        serializer.save(request_type=PhoneConfirmation.REQUEST_PASSWORD)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    # def get(self, request, *args, **kwargs):
    #     """
    #     Requests new sms confirmation for password changing.
    #     Call this method before you reset your password.
    #
    #     """
    #     PhoneConfirmation.objects.create(user=self.request.user,
    #                                      request_type=PhoneConfirmation.REQUEST_PASSWORD)
    #     # TODO(VM): Send message to phone
    #     return Response({
    #         'message': 'sms code has been sent to your phone'
    #     })
    #
    # def post(self, request, *args, **kwargs):
    #     """
    #     Method for changing password.
    #
    #     ---
    #     serializer: smsconfirmation.serializers.ChangePasswordSerializer
    #     parameters:
    #         - name: code
    #           description: Code received by SMS
    #         - name: password1
    #           description: New password. Must be great than 5.
    #         - name: password2
    #           description: Password confirmation. Must be equal to password1.
    #     """
    #     return super().post(*args, **kwargs)

    def on_code_confirmed(self, request, confirmation):
        user = User.objects.get(phone=confirmation.phone)

        user.set_password(request.data['password1'])
        user.save()

