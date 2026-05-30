from django.db import models
from django.utils.translation import gettext_lazy as _


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
    currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.PROTECT,
        related_name="hotels",
        verbose_name=_("Currency"),
        null=True,
        blank=True,
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    agency_price = models.DecimalField(_("Agency Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    main_image = models.ImageField(_("Main Image"), upload_to="hotels/main/", blank=True, null=True)
    features = models.ManyToManyField(HotelFeature, blank=True, related_name="hotels", verbose_name=_("Features"))

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotels")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.city})"

    def get_price_for_user(self, user):
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            return self.agency_price
        return self.price


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