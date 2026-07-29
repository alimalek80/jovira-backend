from django.conf import settings
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


class ReservationEmail(models.Model):
    """
    Stores a record of every email sent from within a reservation context.
    Provides a per-reservation email thread history.
    """

    DIRECTION_SENT = 'SENT'
    DIRECTION_CHOICES = [
        (DIRECTION_SENT, 'Sent'),
    ]

    reservation = models.ForeignKey(
        'reservations.Reservation',
        on_delete=models.CASCADE,
        related_name='emails',
        verbose_name='Reservation',
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_reservation_emails',
        verbose_name='Sent By',
    )
    direction = models.CharField(
        max_length=4,
        choices=DIRECTION_CHOICES,
        default=DIRECTION_SENT,
    )
    to_address = models.CharField(max_length=255)
    cc_address = models.CharField(max_length=255, blank=True, default='')
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Reservation Email'
        verbose_name_plural = 'Reservation Emails'
        ordering = ('-sent_at',)

    def __str__(self):
        return f'Email to {self.to_address} re: {self.reservation} ({self.sent_at:%Y-%m-%d %H:%M})'