from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class EmailConfig(models.Model):
    """
    Stores the agency's outgoing SMTP email configuration.
    Only one active config is allowed at a time.
    Password is stored as plaintext for now — restrict API access to ADMIN only.
    """

    ENCRYPTION_TLS = 'TLS'
    ENCRYPTION_SSL = 'SSL'
    ENCRYPTION_NONE = 'NONE'

    ENCRYPTION_CHOICES = [
        (ENCRYPTION_TLS, 'TLS (STARTTLS)'),
        (ENCRYPTION_SSL, 'SSL/TLS'),
        (ENCRYPTION_NONE, 'None'),
    ]

    label = models.CharField(
        max_length=100,
        default='Default Email Config',
        help_text='Friendly name for this configuration',
    )
    smtp_host = models.CharField(max_length=255)
    smtp_port = models.PositiveIntegerField(
        default=587,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    smtp_username = models.CharField(max_length=255)
    smtp_password = models.CharField(max_length=255)
    from_email = models.EmailField(
        help_text='The "From" address shown on outgoing emails',
    )
    from_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Display name shown alongside the from address',
    )
    encryption = models.CharField(
        max_length=4,
        choices=ENCRYPTION_CHOICES,
        default=ENCRYPTION_TLS,
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Only one config should be active at a time',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email Configuration'
        verbose_name_plural = 'Email Configurations'

    def __str__(self):
        return f'{self.label} ({self.from_email})'

    def save(self, *args, **kwargs):
        # Enforce single active config: deactivate all others when this one is set active
        if self.is_active:
            EmailConfig.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)