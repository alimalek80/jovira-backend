from django.apps import AppConfig


class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings'
    label = 'agency_settings'  # avoids clash with Django's built-in 'settings' module