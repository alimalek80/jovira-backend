from django.db import models
from django.utils.translation import gettext_lazy as _


class Hotel(models.Model):
    name = models.CharField(_("Hotel Name"), max_length=255)
    city = models.CharField(_("City"), max_length=120)
    stars = models.IntegerField(_("Stars"))
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="hotels",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotels")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.city})"


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

    class Meta:
        verbose_name = _("Flight")
        verbose_name_plural = _("Flights")
        ordering = ("-departure_time",)

    def __str__(self):
        return f"{self.flight_number} - {self.airline}"


class TourPackage(models.Model):
    name = models.CharField(_("Package Name"), max_length=255)
    destination = models.CharField(_("Destination"), max_length=120)
    days = models.IntegerField(_("Days"))
    nights = models.IntegerField(_("Nights"))
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

    class Meta:
        verbose_name = _("Tour Package")
        verbose_name_plural = _("Tour Packages")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.destination})"

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.public_price


class Excursion(models.Model):
    name = models.CharField(_("Excursion Name"), max_length=255)
    city = models.CharField(_("City"), max_length=120)
    duration_hours = models.DecimalField(_("Duration (Hours)"), max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = _("Excursion")
        verbose_name_plural = _("Excursions")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} - {self.city}"