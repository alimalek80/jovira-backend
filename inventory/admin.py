from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Excursion, Flight, Hotel, TourPackage, HotelFeature, HotelImage, Transfer, TransferProvider



class HotelImageInline(admin.TabularInline):
	model = HotelImage
	extra = 1


@admin.register(Hotel)
class HotelAdmin(TranslationAdmin):
	list_display = ('name', 'city', 'stars', 'currency', 'price')
	search_fields = ('name', 'city')
	list_filter = ('city', 'stars', 'currency')
	filter_horizontal = ('features',)
	inlines = [HotelImageInline]


@admin.register(HotelFeature)
class HotelFeatureAdmin(TranslationAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
	list_display = ('hotel', 'image', 'alt_text', 'order')
	search_fields = ('hotel__name', 'alt_text')


@admin.register(Flight)
class FlightAdmin(TranslationAdmin):
	list_display = ('flight_number', 'airline', 'origin', 'destination', 'departure_time', 'arrival_time', 'currency', 'price')
	search_fields = ('flight_number', 'airline', 'origin', 'destination')
	list_filter = ('airline', 'origin', 'destination', 'currency')


@admin.register(TourPackage)
class TourPackageAdmin(TranslationAdmin):
	list_display = ('name', 'destination', 'days', 'nights')
	search_fields = ('name', 'destination')
	list_filter = ('destination',)


@admin.register(Excursion)
class ExcursionAdmin(TranslationAdmin):
	list_display = ('name', 'city', 'duration_hours')
	search_fields = ('name', 'city')
	list_filter = ('city',)


@admin.register(TransferProvider)
class TransferProviderAdmin(admin.ModelAdmin):
	list_display = ('name', 'provider_type', 'contact_person', 'phone', 'email')
	search_fields = ('name', 'contact_person', 'email')
	list_filter = ('provider_type',)


@admin.register(Transfer)
class TransferAdmin(TranslationAdmin):
	list_display = ('name', 'provider', 'from_location', 'to_location', 'vehicle_type', 'capacity', 'currency', 'public_price', 'agency_price')
	search_fields = ('name', 'from_location', 'to_location', 'provider__name')
	list_filter = ('provider', 'currency')
	autocomplete_fields = ('provider', 'currency')
