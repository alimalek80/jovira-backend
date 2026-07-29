from django.core.mail import send_mail, get_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from accounts.permissions import IsAdminRole
from .models import EmailConfig
from .serializers import (
    EmailConfigSerializer,
    EmailConfigReadSerializer,
    TestEmailSerializer,
)


class EmailConfigViewSet(ModelViewSet):
    """
    CRUD for the agency SMTP email configuration.
    Restricted to ADMIN role only.
    """

    queryset = EmailConfig.objects.all().order_by('-is_active', '-updated_at')
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return EmailConfigSerializer
        return EmailConfigReadSerializer

    @action(detail=True, methods=['post'], url_path='test')
    def test_email(self, request, pk=None):
        """
        Send a test email using this config to verify credentials work.
        POST /api/v1/settings/email-config/{id}/test/
        Body: { "recipient": "someone@example.com" }
        """
        config = self.get_object()
        serializer = TestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient = serializer.validated_data['recipient']

        use_tls = config.encryption == EmailConfig.ENCRYPTION_TLS
        use_ssl = config.encryption == EmailConfig.ENCRYPTION_SSL

        try:
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=config.smtp_host,
                port=config.smtp_port,
                username=config.smtp_username,
                password=config.smtp_password,
                use_tls=use_tls,
                use_ssl=use_ssl,
            )

            from_address = (
                f'{config.from_name} <{config.from_email}>'
                if config.from_name
                else config.from_email
            )

            send_mail(
                subject='Jovira — Test Email',
                message=(
                    'This is a test email sent from Jovira to verify '
                    'your SMTP configuration is working correctly.'
                ),
                from_email=from_address,
                recipient_list=[recipient],
                connection=connection,
                fail_silently=False,
            )

            return Response(
                {'detail': f'Test email sent successfully to {recipient}.'},
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {'detail': f'Failed to send test email: {str(exc)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ReservationEmailViewSet(ViewSet):
    """
    Compose and send emails from within a reservation context.
    Accessible to all authenticated staff roles.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='send')
    def send(self, request):
        """
        Send an email using the active EmailConfig.
        POST /api/v1/settings/reservation-email/send/
        Body: {
            "to": "hotel@example.com",
            "cc": "optional@example.com",
            "subject": "Reservation request #12345",
            "body": "Dear Sir/Madam..."
        }
        """
        to = request.data.get('to', '').strip()
        cc = request.data.get('cc', '').strip()
        subject = request.data.get('subject', '').strip()
        body = request.data.get('body', '').strip()

        if not to:
            return Response(
                {'detail': 'Recipient email (to) is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not subject:
            return Response(
                {'detail': 'Subject is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not body:
            return Response(
                {'detail': 'Email body is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = EmailConfig.objects.filter(is_active=True).first()
        if not config:
            return Response(
                {'detail': 'No active email configuration found. Please configure SMTP settings first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_tls = config.encryption == EmailConfig.ENCRYPTION_TLS
        use_ssl = config.encryption == EmailConfig.ENCRYPTION_SSL

        try:
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=config.smtp_host,
                port=config.smtp_port,
                username=config.smtp_username,
                password=config.smtp_password,
                use_tls=use_tls,
                use_ssl=use_ssl,
            )

            from_address = (
                f'{config.from_name} <{config.from_email}>'
                if config.from_name
                else config.from_email
            )

            recipient_list = [to]
            if cc:
                recipient_list.append(cc)

            send_mail(
                subject=subject,
                message=body,
                from_email=from_address,
                recipient_list=recipient_list,
                connection=connection,
                fail_silently=False,
            )

            return Response(
                {'detail': f'Email sent successfully to {to}.'},
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {'detail': f'Failed to send email: {str(exc)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )