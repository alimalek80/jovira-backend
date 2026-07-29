from django.core.mail import send_mail, get_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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

        # Build connection from stored config
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