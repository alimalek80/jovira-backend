from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Excursion, Flight, Hotel, TourPackage


@admin.register(Hotel)
class HotelAdmin(TranslationAdmin):
	list_display = ('name', 'city', 'stars', 'currency', 'price')
	search_fields = ('name', 'city')
	list_filter = ('city', 'stars', 'currency')


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
