from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from agencies.models import Agency
from inventory.models import Excursion, Flight, Hotel, HotelRoom, TourPackage, Transfer


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
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_reservations",
        verbose_name=_("Assigned To"),
        null=True,
        blank=True,
        help_text=_("The internal staff member currently responsible for handling this reservation."),
    )
    tour_package = models.ForeignKey(
        TourPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
        verbose_name=_("Tour Package"),
    )
    # New field for Ping-Pong workflow
    is_locked_by_finance = models.BooleanField(
        _("Locked by Finance"),
        default=False,
        help_text=_("When true, only Finance/Admin users can modify this reservation. Sales/Reservation staff get read-only access.")
    )

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        ordering = ("-created_at",)

    def __str__(self):
        return self.reservation_number


class ReservationActivityLog(models.Model):
    class ActionChoices(models.TextChoices):
        CREATED = "CREATED", _("Created")
        UPDATED = "UPDATED", _("Updated")
        STATUS_CHANGED = "STATUS_CHANGED", _("Status Changed")
        FINANCE_LOCKED = "FINANCE_LOCKED", _("Finance Locked")
        FINANCE_UNLOCKED = "FINANCE_UNLOCKED", _("Finance Unlocked")
        TOURIST_ADDED = "TOURIST_ADDED", _("Tourist Added")
        HOTEL_BOOKING_ADDED = "HOTEL_BOOKING_ADDED", _("Hotel Booking Added")
        HOTEL_BOOKING_UPDATED = "HOTEL_BOOKING_UPDATED", _("Hotel Booking Updated")
        FLIGHT_TICKET_ADDED = "FLIGHT_TICKET_ADDED", _("Flight Ticket Added")
        TRANSFER_SERVICE_ADDED = "TRANSFER_SERVICE_ADDED", _("Transfer Service Added")
        EXCURSION_BOOKING_ADDED = "EXCURSION_BOOKING_ADDED", _("Excursion Booking Added")
        EXCURSION_SERVICE_ADDED = "EXCURSION_SERVICE_ADDED", _("Excursion Service Added")

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="activity_logs",
        verbose_name=_("Reservation"),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservation_activity_logs",
        verbose_name=_("Actor"),
    )
    action = models.CharField(
        _("Action"),
        max_length=50,
        choices=ActionChoices.choices,
    )
    message = models.TextField(_("Message"), blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Reservation Activity Log")
        verbose_name_plural = _("Reservation Activity Logs")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["reservation", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.action}"


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
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELLED = "CANCELLED", _("Cancelled")

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="hotel_bookings",
        verbose_name=_("Reservation"),
    )
    hotel_room = models.ForeignKey(
        HotelRoom,
        on_delete=models.PROTECT,
        related_name="hotel_bookings",
        verbose_name=_("Hotel Room"),
    )
    check_in_date = models.DateField(_("Check-in Date"))
    check_out_date = models.DateField(_("Check-out Date"))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    tourists = models.ManyToManyField(
        Tourist,
        related_name="hotel_bookings",
        verbose_name=_("Tourists"),
        blank=True,
    )

    # Financials
    selling_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="hotel_bookings_selling",
        verbose_name=_("Selling Currency"),
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        _("Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    agency_price = models.DecimalField(
        _("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="hotel_bookings_cost",
        verbose_name=_("Cost Currency"),
        null=True,
        blank=True,
    )
    cost = models.DecimalField(
        _("Cost"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cross_currency_rate = models.DecimalField(
        _("Cross Currency Rate"),
        max_digits=15,
        decimal_places=10,
        default=Decimal("1.0000000000"),
    )

    # Tracking
    confirm_booking_number = models.CharField(
        _("Confirm Booking Number"), max_length=50, blank=True
    )
    agent_confirmation_number = models.CharField(
        _("Agent Confirmation Number"), max_length=50, blank=True
    )
    hotel_cancellation_number = models.CharField(
        _("Hotel Cancellation Number"), max_length=50, blank=True
    )

    # Notes
    internal_note = models.TextField(_("Internal Note"), blank=True)
    remarks_for_hotel = models.TextField(_("Remarks for Hotel"), blank=True)

    is_paid = models.BooleanField(_("Is Paid"), default=False)

    class Meta:
        verbose_name = _("Hotel Booking")
        verbose_name_plural = _("Hotel Bookings")
        ordering = ("check_in_date",)

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.hotel_room}"


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
    departure_date = models.DateField(
        _("Departure Date"),
        null=True,
        blank=True,
    )
    arrival_date = models.DateField(
        _("Arrival Date"),
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        _("Price"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="flight_tickets",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    paid = models.BooleanField(_("Paid"), default=False)
    cost = models.DecimalField(
        _("Cost"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="flight_tickets_cost",
        verbose_name=_("Cost Currency"),
        null=True,
        blank=True,
    )
    cross_currency_rate = models.DecimalField(
        _("Cross Currency Rate"),
        max_digits=15,
        decimal_places=10,
        default=Decimal("1.0000000000"),
    )

    class Meta:
        verbose_name = _("Flight Ticket")
        verbose_name_plural = _("Flight Tickets")
        ordering = ("id",)

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.flight.flight_number}"

class OtherService(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="other_services",
        verbose_name=_("Reservation"),
    )
    system_date = models.DateTimeField(_("System Date"), auto_now_add=True)
    service_date = models.DateField(_("Service Date"))
    service_name = models.CharField(_("Service Name"), max_length=255)
    selling_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="other_services_selling",
        verbose_name=_("Selling Currency"),
        null=True,
        blank=True,
    )
    cost_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="other_services_cost",
        verbose_name=_("Cost Currency"),
        null=True,
        blank=True,
    )
    cross_currency_rate = models.DecimalField(
        _("Cross Currency Rate"),
        max_digits=15,
        decimal_places=10,
        default=Decimal("1.0000000000"),
    )
    price = models.DecimalField(
        _("Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost = models.DecimalField(
        _("Cost"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    is_paid = models.BooleanField(_("Is Paid"), default=False)
    note = models.TextField(_("Note"), blank=True)

    class Meta:
        verbose_name = _("Other Service")
        verbose_name_plural = _("Other Services")
        ordering = ("-system_date",)

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.service_name}"

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
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        verbose_name=_("Transfer (Catalog)"),
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
    agency_price = models.DecimalField(_("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    cost = models.DecimalField(
        _("Cost"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="transfer_services_cost",
        verbose_name=_("Cost Currency"),
        null=True,
        blank=True,
    )
    cross_currency_rate = models.DecimalField(
        _("Cross Currency Rate"),
        max_digits=15,
        decimal_places=10,
        default=Decimal("1.0000000000"),
    )
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


class ExcursionService(models.Model):
    """Standalone excursion booking with full financial tracking."""

    system_date = models.DateTimeField(_("System Date"), auto_now_add=True)
    excursion_date = models.DateField(_("Excursion Date"))
    excursion = models.ForeignKey(
        Excursion,
        on_delete=models.PROTECT,
        related_name="excursion_services",
        verbose_name=_("Excursion"),
    )
    is_combo = models.BooleanField(_("Is Combo"), default=False)
    pickup_point = models.CharField(_("Pickup Point"), max_length=255, blank=True, null=True)

    # Financials
    price = models.DecimalField(
        _("Price"), max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    selling_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="excursion_services_selling",
        verbose_name=_("Selling Currency"),
    )
    cost = models.DecimalField(
        _("Cost"), max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    cost_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="excursion_services_cost",
        verbose_name=_("Cost Currency"),
    )
    cross_currency_rate = models.DecimalField(
        _("Cross Currency Rate"),
        max_digits=15,
        decimal_places=10,
        default=Decimal("1.0000000000"),
    )
    is_paid = models.BooleanField(_("Is Paid"), default=False)

    # Tracking
    confirm_booking_number = models.CharField(
        _("Confirm Booking Number"), max_length=50, blank=True, null=True
    )
    agent_confirmation_number = models.CharField(
        _("Agent Confirmation Number"), max_length=50, blank=True, null=True
    )
    note = models.TextField(_("Note"), blank=True, null=True)

    class Meta:
        verbose_name = _("Excursion Service")
        verbose_name_plural = _("Excursion Services")
        ordering = ("-excursion_date",)

    def __str__(self):
        return f"{self.excursion.name} - {self.excursion_date}"