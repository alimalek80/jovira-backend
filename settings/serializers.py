from rest_framework import serializers
from .models import EmailConfig, ReservationEmail


class EmailConfigSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = EmailConfig
        fields = [
            'id',
            'label',
            'smtp_host',
            'smtp_port',
            'smtp_username',
            'smtp_password',
            'from_email',
            'from_name',
            'encryption',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailConfigReadSerializer(serializers.ModelSerializer):
    """
    Safe read serializer — never exposes smtp_password.
    Used for GET responses.
    """

    class Meta:
        model = EmailConfig
        fields = [
            'id',
            'label',
            'smtp_host',
            'smtp_port',
            'smtp_username',
            'from_email',
            'from_name',
            'encryption',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class TestEmailSerializer(serializers.Serializer):
    recipient = serializers.EmailField(
        help_text='Email address to send the test message to',
    )

class ReservationEmailSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ReservationEmail
        fields = [
            'id',
            'reservation',
            'sent_by',
            'sent_by_name',
            'direction',
            'to_address',
            'cc_address',
            'subject',
            'body',
            'sent_at',
            'is_successful',
            'error_message',
        ]
        read_only_fields = fields

    def get_sent_by_name(self, obj):
        if obj.sent_by:
            return obj.sent_by.get_full_name() or obj.sent_by.email
        return None