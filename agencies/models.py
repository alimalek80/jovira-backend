from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Agency(models.Model):
    name = models.CharField(_("Agency Name"), max_length=255)
    agency_type = models.CharField(_("Agency Type"), max_length=100)
    contact_person = models.CharField(_("Contact Person"), max_length=255)

    email = models.EmailField(_("Email"), max_length=255, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    mobile_phone = models.CharField(_("Mobile Phone"), max_length=50, blank=True, null=True)
    skype_id = models.CharField(_("Skype ID"), max_length=100, blank=True, null=True)
    icq = models.CharField(_("ICQ"), max_length=50, blank=True, null=True)
    is_approved = models.BooleanField(_("Is Approved"), default=False)
    approved_at = models.DateTimeField(_("Approved At"), blank=True, null=True)

    class Meta:
        verbose_name = _("Agency")
        verbose_name_plural = _("Agencies")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def approve(self):
        self.is_approved = True
        if self.approved_at is None:
            self.approved_at = timezone.now()
        self.save(update_fields=("is_approved", "approved_at"))


class Supplier(models.Model):
    class SupplierType(models.TextChoices):
        HOTEL = "HOTEL", _("Hotel")
        TRANSFER = "TRANSFER", _("Transfer Company")
        TOUR_OPERATOR = "TOUR_OPERATOR", _("Tour Operator")
        AIRLINE = "AIRLINE", _("Airline")
        OTHER = "OTHER", _("Other")

    name = models.CharField(_("Supplier Name"), max_length=255)
    supplier_type = models.CharField(
        _("Supplier Type"),
        max_length=20,
        choices=SupplierType.choices,
        default=SupplierType.OTHER,
    )
    email = models.EmailField(_("Email"), blank=True, default="")
    phone = models.CharField(_("Phone"), max_length=50, blank=True, default="")
    address = models.TextField(_("Address"), blank=True, default="")
    tax_number = models.CharField(_("Tax Number"), max_length=100, blank=True, default="")
    default_currency = models.ForeignKey(
        "finance.Currency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suppliers",
        verbose_name=_("Default Currency"),
    )
    bank_details = models.TextField(_("Bank Details"), blank=True, default="")
    note = models.TextField(_("Note"), blank=True, default="")
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ("name",)

    def __str__(self):
        return self.name
