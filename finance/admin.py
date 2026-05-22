from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Currency, ExchangeRate, Invoice


@admin.register(Currency)
class CurrencyAdmin(TranslationAdmin):
	list_display = ('code', 'name', 'symbol', 'is_active')
	search_fields = ('code', 'name', 'symbol')
	list_filter = ('is_active',)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
	list_display = ('base_currency', 'target_currency', 'rate', 'last_updated')
	search_fields = ('base_currency__code', 'target_currency__code')
	list_filter = ('base_currency', 'target_currency', 'last_updated')
	autocomplete_fields = ('base_currency', 'target_currency')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
	list_display = ('reservation', 'net_amount', 'sale_amount', 'profit', 'agency_commission', 'is_paid')
	list_filter = ('is_paid',)
	search_fields = ('reservation__reservation_number',)
	autocomplete_fields = ('reservation',)
