from django.contrib import admin
from django import forms
from modeltranslation.admin import TranslationAdmin
from decimal import Decimal
from finance.utils import convert_amount

from .models import Excursion, Flight, Hotel, TourPackage, HotelFeature, HotelImage, Transfer, TransferProvider



class HotelImageInline(admin.TabularInline):
	model = HotelImage
	extra = 1


@admin.register(Hotel)
class HotelAdmin(TranslationAdmin):
	list_display = ('name', 'city', 'stars', 'currency', 'price', 'agency_price', 'cost_price')
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
	list_display = ('flight_number', 'airline', 'origin', 'destination', 'departure_time', 'arrival_time', 'currency', 'price', 'agency_price', 'cost_price')
	search_fields = ('flight_number', 'airline', 'origin', 'destination')
	list_filter = ('airline', 'origin', 'destination', 'currency')


class TourPackageAdminForm(forms.ModelForm):
	minimum_cost_floor = forms.DecimalField(
		label="Minimum Cost Floor",
		required=False,
		disabled=True,
		decimal_places=2,
		max_digits=12,
		help_text="This amount is the no-profit floor based on selected components. Public/agency/cost prices cannot be lower than this value.",
	)

	class Meta:
		model = TourPackage
		fields = "__all__"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.instance and self.instance.pk:
			self.fields["minimum_cost_floor"].initial = self.instance.calculate_minimum_cost_floor()

	def clean(self):
		cleaned_data = super().clean()

		currency = cleaned_data.get("currency")
		nights = cleaned_data.get("nights") or 1
		flights = cleaned_data.get("flights")
		hotels = cleaned_data.get("hotels")
		transfers = cleaned_data.get("transfers")
		excursions = cleaned_data.get("excursions")

		minimum_floor = Decimal("0.00")
		for item in flights or []:
			minimum_floor += convert_amount(item.cost_price or Decimal("0.00"), item.currency_id, getattr(currency, "id", None))

		for item in transfers or []:
			minimum_floor += convert_amount(item.cost_price or Decimal("0.00"), item.currency_id, getattr(currency, "id", None))

		for item in excursions or []:
			minimum_floor += convert_amount(item.cost_price or Decimal("0.00"), item.currency_id, getattr(currency, "id", None))

		nights_multiplier = nights if nights > 0 else 1
		for item in hotels or []:
			minimum_floor += convert_amount((item.cost_price or Decimal("0.00")) * nights_multiplier, item.currency_id, getattr(currency, "id", None))

		minimum_floor = minimum_floor.quantize(Decimal("0.01"))

		self.cleaned_data["minimum_cost_floor"] = minimum_floor

		cost_price = cleaned_data.get("cost_price")
		agency_price = cleaned_data.get("agency_price")
		public_price = cleaned_data.get("public_price")

		if cost_price is not None and cost_price < minimum_floor:
			self.add_error("cost_price", "Cost price cannot be lower than minimum component cost floor.")
		if agency_price is not None and agency_price < minimum_floor:
			self.add_error("agency_price", "Agency price cannot be lower than minimum component cost floor.")
		if public_price is not None and public_price < minimum_floor:
			self.add_error("public_price", "Public price cannot be lower than minimum component cost floor.")
		if public_price is not None and agency_price is not None and public_price < agency_price:
			self.add_error("public_price", "Public price cannot be lower than agency price.")

		return cleaned_data


@admin.register(TourPackage)
class TourPackageAdmin(TranslationAdmin):
	form = TourPackageAdminForm
	list_display = ('name', 'destination', 'days', 'nights', 'currency', 'public_price', 'agency_price', 'cost_price')
	search_fields = ('name', 'destination')
	list_filter = ('destination',)
	filter_horizontal = ('flights', 'hotels', 'transfers', 'excursions')
	fieldsets = (
		(
			'Package Basics',
			{'fields': ('name', 'destination', 'days', 'nights', 'currency')}
		),
		(
			'Optional Components',
			{
				'fields': ('flights', 'hotels', 'transfers', 'excursions'),
				'description': 'Select any components to build the package floor cost. These selections are optional.'
			}
		),
		(
			'Pricing Guidance',
			{
				'fields': ('minimum_cost_floor', 'cost_price', 'agency_price', 'public_price'),
				'description': 'Minimum Cost Floor is no-profit. Selling prices cannot be lower than this calculated amount.'
			}
		),
	)


@admin.register(Excursion)
class ExcursionAdmin(TranslationAdmin):
	list_display = ('name', 'city', 'duration_hours', 'currency', 'public_price', 'agency_price', 'cost_price')
	search_fields = ('name', 'city')
	list_filter = ('city',)


@admin.register(TransferProvider)
class TransferProviderAdmin(admin.ModelAdmin):
	list_display = ('name', 'provider_type', 'contact_person', 'phone', 'email')
	search_fields = ('name', 'contact_person', 'email')
	list_filter = ('provider_type',)


@admin.register(Transfer)
class TransferAdmin(TranslationAdmin):
	list_display = ('name', 'provider', 'from_location', 'to_location', 'vehicle_type', 'capacity', 'currency', 'public_price', 'agency_price', 'cost_price')
	search_fields = ('name', 'from_location', 'to_location', 'provider__name')
	list_filter = ('provider', 'currency')
	autocomplete_fields = ('provider', 'currency')
