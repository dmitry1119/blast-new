# Create your views here.
import logging

from rest_framework import mixins, views
from rest_framework import status, permissions
from rest_framework.response import Response

from smsconfirmation.models import PhoneConfirmation
from smsconfirmation.serializers import (PhoneConfirmationSerializer, ChangePasswordSerializer,
                                         RequestChangePasswordSerializer, SinchVerificationSerializer,
                                         SinchPhoneConfirmationSerializer)
from users.models import User

from smsconfirmation.tasks import (send_verification_request,
                                   send_code_confirmation_request)

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

    # TODO: Make tests
    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']

        confirmation = PhoneConfirmation.objects.get_actual(phone,
                                                            request_type=self.REQUEST_TYPE)

        if not confirmation:
            logger.error('Confirmation request for {} was not found'.format(phone))
            return Response({'code': ['confirmation request was not found']},
                            status=status.HTTP_404_NOT_FOUND)

        if not confirmation.is_actual():
            logger.info('Confirmation code is expired {}'.format(confirmation.pk))
            return Response({
                'code': ['Confirmation code is expired']
            }, status=status.HTTP_400_BAD_REQUEST)

        if confirmation.code == serializer.data['code']:
            confirmation.is_confirmed = True
            confirmation.save()

            self.on_code_confirmed(request, confirmation)

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'code': ['Invalid confirmation code']}, status=status.HTTP_400_BAD_REQUEST)


class PhoneConfirmView(PhoneConfirmBase):
    serializer_class = PhoneConfirmationSerializer

    REQUEST_TYPE = PhoneConfirmation.REQUEST_PHONE

    def get_serializer(self, data):
        if self.request.method == 'POST':
            return PhoneConfirmationSerializer(data=data)

    def post(self, request, *args, **kwargs):
        """
        Requests new phone confirmation code by SMS.
        This method should be called before signing.

        ---
        serializer: smsconfirmation.serializers.PhoneConfirmationSerializer
        parameters:
            - name: phone
              description: phone number with country code (+79131234567 e.g)
        """
        return super().create(request)

    def perform_create(self, serializer):
        serializer.save(request_type=self.REQUEST_TYPE)

    def on_code_confirmed(self, request, confirmation: PhoneConfirmation):
        user = User.objects.get(phone=confirmation.phone)
        user.is_verified = True
        user.save()


class ResetPasswordView(PhoneConfirmBase):

    serializer_class = ChangePasswordSerializer

    REQUEST_TYPE = PhoneConfirmation.REQUEST_PASSWORD

    def get_serializer(self, data):
        if self.request.method == 'POST':
            return RequestChangePasswordSerializer(data=data)
        else:
            return ChangePasswordSerializer(data=data)

    def perform_create(self, serializer):
        serializer.save(request_type=self.REQUEST_TYPE)

    def post(self, request, *args, **kwargs):
        """
        Initial password changing and send confirmation code to user phone.

        ---
        serializer: smsconfirmation.serializers.RequestChangePasswordSerializer
        parameters:
            - name: phone
              description: phone number (+79528048941 for e.g)
        """
        return super().post(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Method for changing password.
        You must request confirmation code before changing your password.

        ---
        serializer: smsconfirmation.serializers.ChangePasswordSerializer
        parameters:
            - name: code
              description: Code received by SMS
            - name: password1
              description: New password. Must be great than 5.
            - name: password2
              description: Password confirmation. Must be equal to password1.
        """
        return self.update(request, *args, **kwargs)

    def on_code_confirmed(self, request, confirmation):
        user = User.objects.get(phone=confirmation.phone)

        user.set_password(request.data['password1'])
        user.save()


class SinchPhoneConfirmationView(views.APIView):

    def post(self, request):
        """
        Requests new phone verification code

        ---
        serializer: smsconfirmation.serializers.PhoneConfirmationSerializer
        """
        serializer = PhoneConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request_type=PhoneConfirmation.REQUEST_PHONE)

        send_verification_request.delay(serializer.data['phone'])

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        """


        ---
        serializer: smsconfirmation.serializers.SinchPhoneConfirmationSerializer
        """
        serializer = SinchPhoneConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        send_code_confirmation_request.delay(serializer.data['code'],
                                             serializer.data['phone'])

        return Response()


class SinchResponseView(views.APIView):

    serializer_class = SinchVerificationSerializer

    def post(self, request, *args, **kwargs):
        print('Request data is', request.data)
        if request.data['method'] != 'sms':
            print('Wrong sinch method')
            return Response()

        is_successfull = request.data['status'] == 'SUCCESSFUL'

        number = request.data['identity']['number']

        confirm = PhoneConfirmation.objects.get_actual(phone=number)
        confirm.is_confirmed = is_successfull
        confirm.save()

        return Response()