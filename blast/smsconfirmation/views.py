# Create your views here.
import logging
from rest_framework.permissions import AllowAny

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions

from smsconfirmation.models import PhoneConfirmation
from smsconfirmation.serializers import PhoneConfirmationSerializer


logger = logging.getLogger(__name__)


class PhoneConfirmView(APIView):
    # TODO (VM): Add is_delivered to filter?
    queryset = PhoneConfirmation.objects.filter(is_confirmed=False)

    def post(self, request):
        serializer = PhoneConfirmationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'message': 'Failed to confirm phone',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        confirmation = self.queryset.filter(user=request.user.pk)
        confirmation = confirmation.order_by('created_at').first()

        if not confirmation:
            logger.error('Confirmation request for user {} was not found'.format(request.user))
            return Response({'message': 'confirmation request was not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if not confirmation.is_actual():
            return Response({
                'message': 'confirmation request outdated'
            }, status=status.HTTP_400_BAD_REQUEST)

        if confirmation.code == serializer.data['code']:
            confirmation.is_confirmed = True
            confirmation.save()

            # TODO: Move to confirmatio.save()?
            request.user.is_confirm = True
            request.user.save()

            return Response({
                'message': 'confirmed'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'wrong code'
            }, status=status.HTTP_400_BAD_REQUEST)


