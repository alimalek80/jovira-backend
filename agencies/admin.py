from django.contrib import admin
from .models import Agency


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
	list_display = ('name', 'agency_type', 'contact_person')
	search_fields = ('name', 'agency_type', 'contact_person')
	list_filter = ('agency_type',)
