from django.contrib import admin
from .models import EmailConfig


@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ['label', 'smtp_host', 'smtp_port', 'from_email', 'encryption', 'is_active', 'updated_at']
    list_filter = ['is_active', 'encryption']
    readonly_fields = ['created_at', 'updated_at']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        # Move smtp_password to end for clarity
        if 'smtp_password' in fields:
            fields = [f for f in fields if f != 'smtp_password'] + ['smtp_password']
        return fields