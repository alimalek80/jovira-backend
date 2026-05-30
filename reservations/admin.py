from django.contrib import admin
from .models import ExcursionBooking, ExcursionService, FlightTicket, HotelBooking, Reservation, Tourist, TransferService


class TouristInline(admin.TabularInline):
	model = Tourist
	extra = 0


class HotelBookingInline(admin.TabularInline):
	model = HotelBooking
	extra = 0


class TransferServiceInline(admin.TabularInline):
	model = TransferService
	extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = ('reservation_number', 'agency', 'currency', 'status', 'created_at')
	list_filter = ('currency', 'status', 'created_at')
	search_fields = ('reservation_number', 'agency__name')
	autocomplete_fields = ('agency', 'currency', 'tour_package')
	inlines = (TouristInline, HotelBookingInline, TransferServiceInline)
	readonly_fields = ('created_at',)


@admin.register(Tourist)
class TouristAdmin(admin.ModelAdmin):
	list_display = ('first_name', 'last_name', 'reservation', 'sex', 'age_type')
	list_filter = ('sex', 'age_type')
	search_fields = ('first_name', 'last_name', 'reservation__reservation_number')
	autocomplete_fields = ('reservation',)


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
	list_display = ('reservation', 'hotel', 'check_in_date', 'check_out_date', 'board_type', 'is_paid')
	list_filter = ('board_type', 'is_paid', 'check_in_date')
	search_fields = ('reservation__reservation_number', 'hotel__name')
	autocomplete_fields = ('reservation', 'hotel')


@admin.register(FlightTicket)
class FlightTicketAdmin(admin.ModelAdmin):
	list_display = ('reservation', 'tourist', 'flight', 'ticket_number', 'pnr_code')
	search_fields = (
		'reservation__reservation_number',
		'tourist__first_name',
		'tourist__last_name',
		'flight__flight_number',
		'ticket_number',
		'pnr_code',
	)
	autocomplete_fields = ('reservation', 'tourist', 'flight')


@admin.register(ExcursionBooking)
class ExcursionBookingAdmin(admin.ModelAdmin):
	list_display = ('reservation', 'excursion', 'tour_date', 'pickup_time')
	list_filter = ('tour_date',)
	search_fields = ('reservation__reservation_number', 'excursion__name')
	autocomplete_fields = ('reservation', 'excursion', 'tourists')


@admin.register(TransferService)
class TransferServiceAdmin(admin.ModelAdmin):
	list_display = (
		'reservation',
		'service_name',
		'service_date',
		'on_arrival',
		'on_departure',
		'from_location_type',
		'to_location_type',
		'price',
		'currency',
	)
	list_filter = ('service_date', 'on_arrival', 'on_departure', 'currency')
	search_fields = ('reservation__reservation_number', 'service_name', 'from_location_name', 'to_location_name')
	autocomplete_fields = ('reservation', 'tour_package', 'currency', 'passengers')


@admin.register(ExcursionService)
class ExcursionServiceAdmin(admin.ModelAdmin):
	list_display = (
		'excursion',
		'excursion_date',
		'is_combo',
		'price',
		'selling_currency',
		'cost',
		'cost_currency',
		'is_paid',
		'system_date',
	)
	list_filter = ('excursion_date', 'is_paid', 'is_combo', 'selling_currency', 'cost_currency')
	search_fields = ('excursion__name', 'confirm_booking_number', 'agent_confirmation_number')
	autocomplete_fields = ('excursion', 'selling_currency', 'cost_currency')
	readonly_fields = ('system_date',)
