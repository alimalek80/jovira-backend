from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from agencies.models import Agency
from inventory.models import Excursion, Flight, Hotel, TourPackage


class Reservation(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        ON_PROCESS = "ON_PROCESS", _("On Process")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELED = "CANCELED", _("Canceled")

    reservation_number = models.CharField(_("Reservation Number"), max_length=100, unique=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name=_("Currency"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    agency = models.ForeignKey(
        Agency,
        on_delete=models.SET_NULL,
        related_name="reservations",
        verbose_name=_("Agency"),
        null=True,
        blank=True,
    )
    tour_package = models.ForeignKey(
        TourPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
        verbose_name=_("Tour Package"),
    )

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        ordering = ("-created_at",)

    def __str__(self):
        return self.reservation_number


class Tourist(models.Model):
    class SexChoices(models.TextChoices):
        MALE = "MALE", _("Male")
        FEMALE = "FEMALE", _("Female")

    class AgeTypeChoices(models.TextChoices):
        ADULT = "ADULT", _("Adult")
        CHILD = "CHILD", _("Child")
        INFANT = "INFANT", _("Infant")

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tourists",
        verbose_name=_("Reservation"),
    )
    first_name = models.CharField(_("First Name"), max_length=150)
    last_name = models.CharField(_("Last Name"), max_length=150)
    sex = models.CharField(_("Sex"), max_length=10, choices=SexChoices.choices)
    age_type = models.CharField(_("Age Type"), max_length=10, choices=AgeTypeChoices.choices)
    passport_number = models.CharField(
        _("Passport Number"),
        max_length=50,
        blank=True,
        help_text=_("Passport number of the tourist, if available."),
    )
    nationality = models.CharField(
        _("Nationality"),
        max_length=100,
        blank=True,
        help_text=_("Nationality of the tourist, if available."),
    )
    birth_date = models.DateField(
        _("Birth Date"),
        null=True,
        blank=True,
        help_text=_("Date of birth of the tourist, if available."),
    )
    passport_expiry_date = models.DateField(
        _("Passport Expiry Date"),
        null=True,
        blank=True,
        help_text=_("Passport expiry date of the tourist, if available."),
    )

    class Meta:
        verbose_name = _("Tourist")
        verbose_name_plural = _("Tourists")
        ordering = ("id",)

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}"
        if self.passport_number:
            return f"{full_name} ({self.passport_number})"
        return full_name


class HotelBooking(models.Model):
    class BoardTypeChoices(models.TextChoices):
        BB = "BB", _("BB")
        HB = "HB", _("HB")
        ALL = "ALL", _("ALL")

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="hotel_bookings",
        verbose_name=_("Reservation"),
    )
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        related_name="hotel_bookings",
        verbose_name=_("Hotel"),
    )
    check_in_date = models.DateField(_("Check-in Date"))
    check_out_date = models.DateField(_("Check-out Date"))
    board_type = models.CharField(
        _("Board Type"),
        max_length=10,
        choices=BoardTypeChoices.choices,
        default=BoardTypeChoices.BB,
    )
    is_paid = models.BooleanField(_("Is Paid"), default=False)

    class Meta:
        verbose_name = _("Hotel Booking")
        verbose_name_plural = _("Hotel Bookings")
        ordering = ("check_in_date",)

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.hotel.name}"


class FlightTicket(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="flight_tickets",
        verbose_name=_("Reservation"),
    )
    flight = models.ForeignKey(
        Flight,
        on_delete=models.PROTECT,
        related_name="flight_tickets",
        verbose_name=_("Flight"),
    )
    tourist = models.ForeignKey(
        Tourist,
        on_delete=models.CASCADE,
        related_name="flight_tickets",
        verbose_name=_("Tourist"),
    )
    ticket_number = models.CharField(_("Ticket Number"), max_length=100, blank=True)
    pnr_code = models.CharField(_("PNR Code"), max_length=50, blank=True)

    class Meta:
        verbose_name = _("Flight Ticket")
        verbose_name_plural = _("Flight Tickets")
        ordering = ("id",)

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.flight.flight_number}"


class ExcursionBooking(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="excursion_bookings",
        verbose_name=_("Reservation"),
    )
    excursion = models.ForeignKey(
        Excursion,
        on_delete=models.PROTECT,
        related_name="excursion_bookings",
        verbose_name=_("Excursion"),
    )
    tourists = models.ManyToManyField(
        Tourist,
        related_name="excursion_bookings",
        verbose_name=_("Tourists"),
    )
    tour_date = models.DateField(_("Tour Date"))
    pickup_time = models.TimeField(_("Pickup Time"), null=True, blank=True)

    class Meta:
        verbose_name = _("Excursion Booking")
        verbose_name_plural = _("Excursion Bookings")
        ordering = ("tour_date",)

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.excursion.name}"


class TransferService(models.Model):
    class LocationTypeChoices(models.TextChoices):
        AIRPORT = "AIRPORT", _("Airport")
        TERMINAL = "TERMINAL", _("Terminal")
        HOTEL = "HOTEL", _("Hotel")

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="transfer_services",
        verbose_name=_("Reservation"),
    )
    tour_package = models.ForeignKey(
        TourPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfer_services",
        verbose_name=_("Tour Package"),
    )
    service_name = models.CharField(_("Service Name"), max_length=255)
    service_date = models.DateField(_("Service Date"))
    on_arrival = models.BooleanField(_("On Arrival"), default=False)
    on_departure = models.BooleanField(_("On Departure"), default=False)
    from_location_type = models.CharField(
        _("From Location Type"),
        max_length=20,
        choices=LocationTypeChoices.choices,
    )
    from_location_name = models.CharField(_("From Location Name"), max_length=255)
    to_location_type = models.CharField(
        _("To Location Type"),
        max_length=20,
        choices=LocationTypeChoices.choices,
    )
    to_location_name = models.CharField(_("To Location Name"), max_length=255)
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="transfer_services",
        verbose_name=_("Currency"),
    )
    passengers = models.ManyToManyField(
        Tourist,
        related_name="transfer_services",
        verbose_name=_("Passengers"),
    )
    external_note = models.TextField(_("External Note"), blank=True)
    driver_note = models.TextField(_("Driver Note"), blank=True)

    class Meta:
        verbose_name = _("Transfer Service")
        verbose_name_plural = _("Transfer Services")
        ordering = ("service_date", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(on_arrival=True) | Q(on_departure=True),
                name="transfer_at_least_one_direction",
            )
        ]

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.service_name}"