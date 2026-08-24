from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class TransferProvider(models.Model):
    class ProviderTypeChoices(models.TextChoices):
        COMPANY = "COMPANY", _("Company")
        INDIVIDUAL = "INDIVIDUAL", _("Individual")

    name = models.CharField(_("Provider Name"), max_length=255)
    provider_type = models.CharField(
        _("Provider Type"),
        max_length=20,
        choices=ProviderTypeChoices.choices,
        default=ProviderTypeChoices.COMPANY,
    )
    contact_person = models.CharField(_("Contact Person"), max_length=255, blank=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Transfer Provider")
        verbose_name_plural = _("Transfer Providers")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class Transfer(models.Model):
    provider = models.ForeignKey(
        TransferProvider,
        on_delete=models.PROTECT,
        related_name="transfers",
        verbose_name=_("Provider"),
    )
    name = models.CharField(_("Transfer Name"), max_length=255)
    from_location = models.CharField(_("From Location"), max_length=255)
    to_location = models.CharField(_("To Location"), max_length=255)
    vehicle_type = models.CharField(_("Vehicle Type"), max_length=100, blank=True)
    capacity = models.PositiveIntegerField(_("Capacity"), null=True, blank=True)
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="transfers",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    public_price = models.DecimalField(_("Public Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    agency_price = models.DecimalField(_("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(_("Cost Price"), max_digits=12, decimal_places=2, null=True, blank=True, help_text=_("Internal procurement cost paid by Jovira. Not visible to agencies or public."))

    class Meta:
        verbose_name = _("Transfer")
        verbose_name_plural = _("Transfers")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.from_location} → {self.to_location})"

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.public_price


class HotelFeature(models.Model):
    name = models.CharField(_("Feature Name"), max_length=100)

    class Meta:
        verbose_name = _("Hotel Feature")
        verbose_name_plural = _("Hotel Features")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Hotel(models.Model):
    name = models.CharField(_("Hotel Name"), max_length=255)
    city = models.CharField(_("City"), max_length=120)
    stars = models.IntegerField(_("Stars"))
    description = models.TextField(_("Description"), blank=True, null=True)
    main_image = models.ImageField(_("Main Image"), upload_to="hotels/main/", blank=True, null=True)
    features = models.ManyToManyField(HotelFeature, blank=True, related_name="hotels", verbose_name=_("Features"))

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotels")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.city})"


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(_("Gallery Image"), upload_to="hotels/gallery/")
    alt_text = models.CharField(_("Alt Text"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Hotel Gallery Image")
        verbose_name_plural = _("Hotel Gallery Images")
        ordering = ("order", "id")

    def __str__(self):
        return f"{self.hotel.name} - {self.alt_text or self.image.url}"


class HotelRoom(models.Model):
    class RoomTypeChoices(models.TextChoices):
        SINGLE = "SINGLE", _("Single")
        DOUBLE = "DOUBLE", _("Double")
        TRIPLE = "TRIPLE", _("Triple")
        FAMILY = "FAMILY", _("Family")
        SUITE = "SUITE", _("Suite")

    class BoardTypeChoices(models.TextChoices):
        RO = "RO", _("RO (Room Only)")
        BB = "BB", _("BB (Bed & Breakfast)")
        HB = "HB", _("HB (Half Board)")
        FB = "FB", _("FB (Full Board)")
        ALL = "ALL", _("All Inclusive")
        UALL = "UALL", _("Ultra All Inclusive")

    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name=_("Hotel"),
    )
    room_type = models.CharField(
        _("Room Type"),
        max_length=20,
        choices=RoomTypeChoices.choices,
    )
    board_type = models.CharField(
        _("Board Type"),
        max_length=10,
        choices=BoardTypeChoices.choices,
    )
    date_from = models.DateField(_("Date From"))
    date_to = models.DateField(_("Date To"))
    availability_count = models.PositiveIntegerField(_("Availability Count"), default=0)
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="hotel_rooms",
        verbose_name=_("Currency"),
    )
    public_price = models.DecimalField(_("Public Price"), max_digits=12, decimal_places=2)
    agency_price = models.DecimalField(
        _("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost_price = models.DecimalField(
        _("Cost Price"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Internal procurement cost paid by Jovira. Not visible to agencies or public."),
    )
    note = models.TextField(_("Note"), blank=True)

    class Meta:
        verbose_name = _("Hotel Room")
        verbose_name_plural = _("Hotel Rooms")
        ordering = ("hotel", "date_from", "room_type")

    def __str__(self):
        return (
            f"{self.hotel.name} — {self.get_room_type_display()} / "
            f"{self.get_board_type_display()} [{self.date_from} – {self.date_to}]"
        )

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.public_price


class Flight(models.Model):
    flight_number = models.CharField(_("Flight Number"), max_length=50)
    airline = models.CharField(_("Airline"), max_length=120)
    origin = models.CharField(_("Origin"), max_length=120)
    destination = models.CharField(_("Destination"), max_length=120)
    departure_time = models.DateTimeField(_("Departure Time"))
    arrival_time = models.DateTimeField(_("Arrival Time"))
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="flights",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    agency_price = models.DecimalField(_("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(_("Cost Price"), max_digits=12, decimal_places=2, null=True, blank=True, help_text=_("Internal procurement cost paid by Jovira. Not visible to agencies or public."))

    class Meta:
        verbose_name = _("Flight")
        verbose_name_plural = _("Flights")
        ordering = ("-departure_time",)

    def __str__(self):
        return f"{self.flight_number} - {self.airline}"

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.price


class TourPackage(models.Model):
    name = models.CharField(_("Package Name"), max_length=255)
    destination = models.CharField(_("Destination"), max_length=120)
    days = models.IntegerField(_("Days"))
    nights = models.IntegerField(_("Nights"))
    main_image = models.ImageField(_("Main Image"), upload_to="tour_packages/main/", blank=True, null=True)
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="tour_packages",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    public_price = models.DecimalField(
        _("Public Price"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    agency_price = models.DecimalField(
        _("Agency Price"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    cost_price = models.DecimalField(
        _("Cost Price"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Internal procurement cost paid by Jovira. Not visible to agencies or public."),
    )
    flights = models.ManyToManyField(
        "Flight",
        blank=True,
        related_name="tour_packages",
        verbose_name=_("Flights"),
    )
    hotels = models.ManyToManyField(
        "Hotel",
        blank=True,
        related_name="tour_packages",
        verbose_name=_("Hotels"),
    )
    transfers = models.ManyToManyField(
        "Transfer",
        blank=True,
        related_name="tour_packages",
        verbose_name=_("Transfers"),
    )
    excursions = models.ManyToManyField(
        "Excursion",
        blank=True,
        related_name="tour_packages",
        verbose_name=_("Excursions"),
    )

    class Meta:
        verbose_name = _("Tour Package")
        verbose_name_plural = _("Tour Packages")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.destination})"

    def calculate_minimum_cost_floor(self):
        if not self.pk:
            return Decimal("0.00")

        from finance.utils import convert_amount

        floor = Decimal("0.00")
        for flight in self.flights.all():
            component_cost = flight.cost_price or Decimal("0.00")
            floor += convert_amount(component_cost, flight.currency_id, self.currency_id)

        for transfer in self.transfers.all():
            component_cost = transfer.cost_price or Decimal("0.00")
            floor += convert_amount(component_cost, transfer.currency_id, self.currency_id)

        for excursion in self.excursions.all():
            component_cost = excursion.cost_price or Decimal("0.00")
            floor += convert_amount(component_cost, excursion.currency_id, self.currency_id)

        return floor.quantize(Decimal("0.01"))

    def clean(self):
        minimum_floor = self.calculate_minimum_cost_floor()

        if self.cost_price is not None and self.cost_price < minimum_floor:
            raise ValidationError({
                "cost_price": _("Cost price cannot be lower than the minimum component cost floor.")
            })

        if self.agency_price is not None and self.agency_price < minimum_floor:
            raise ValidationError({
                "agency_price": _("Agency price cannot be lower than the minimum component cost floor.")
            })

        if self.public_price is not None and self.public_price < minimum_floor:
            raise ValidationError({
                "public_price": _("Public price cannot be lower than the minimum component cost floor.")
            })

        if self.public_price is not None and self.agency_price is not None and self.public_price < self.agency_price:
            raise ValidationError({
                "public_price": _("Public price cannot be lower than agency price.")
            })

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.public_price


class TourPackageGalleryImage(models.Model):
    tour_package = models.ForeignKey(
        TourPackage,
        on_delete=models.CASCADE,
        related_name="gallery_images",
        verbose_name=_("Tour Package"),
    )
    image = models.ImageField(_("Gallery Image"), upload_to="tour_packages/gallery/")
    alt_text = models.CharField(_("Alt Text"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Tour Package Gallery Image")
        verbose_name_plural = _("Tour Package Gallery Images")
        ordering = ("order", "id")

    def __str__(self):
        return f"{self.tour_package.name} - {self.alt_text or self.image.url}"


class Excursion(models.Model):
    name = models.CharField(_("Excursion Name"), max_length=255)
    city = models.CharField(_("City"), max_length=120)
    duration_hours = models.DecimalField(_("Duration (Hours)"), max_digits=5, decimal_places=2)
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="excursions",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    public_price = models.DecimalField(_("Public Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    agency_price = models.DecimalField(_("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(_("Cost Price"), max_digits=12, decimal_places=2, null=True, blank=True, help_text=_("Internal procurement cost paid by Jovira. Not visible to agencies or public."))

    class Meta:
        verbose_name = _("Excursion")
        verbose_name_plural = _("Excursions")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} - {self.city}"

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.public_price