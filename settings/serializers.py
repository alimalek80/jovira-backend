from rest_framework import serializers
from .models import EmailConfig


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