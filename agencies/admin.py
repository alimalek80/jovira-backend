from django.contrib import admin
from .models import Agency, Supplier


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
	list_display = ('name', 'agency_type', 'contact_person', 'is_approved', 'approved_at')
	search_fields = ('name', 'agency_type', 'contact_person')
	list_filter = ('agency_type', 'is_approved')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	list_display = ('name', 'supplier_type', 'email', 'phone', 'is_active')
	list_filter = ('supplier_type', 'is_active')
	search_fields = ('name', 'email', 'tax_number')
