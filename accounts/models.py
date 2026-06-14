from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    class RoleChoices(models.TextChoices):
        # Public roles
        NORMAL = "NORMAL", _("Normal User")
        AGENCY = "AGENCY", _("Agency")

        # Organizational roles
        ADMIN = "ADMIN", _("Admin")
        SALES = "SALES", _("Sales Staff")
        RESERVATION = "RESERVATION", _("Reservation Manager")
        INVENTORY = "INVENTORY", _("Inventory/Admin Staff")
        FINANCE = "FINANCE", _("Finance/Accounting")

    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Phone Number",
    )

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.NORMAL,
        verbose_name=_("Role"),
    )

    agency = models.ForeignKey(
        "agencies.Agency",
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
        verbose_name=_("Agency"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("id",)

    @property
    def is_admin_role(self):
        return self.is_superuser or self.is_staff or self.role == self.RoleChoices.ADMIN

    @property
    def is_admin_or_finance(self):
        return self.is_admin_role or self.role == self.RoleChoices.FINANCE

    @property
    def is_reservation_staff(self):
        return self.is_admin_role or self.role == self.RoleChoices.RESERVATION

    @property
    def is_inventory_staff(self):
        return self.is_admin_role or self.role == self.RoleChoices.INVENTORY

    @property
    def can_access_agency_prices(self):
        return self.is_admin_role or self.role in {
            self.RoleChoices.AGENCY,
            self.RoleChoices.SALES,
            self.RoleChoices.RESERVATION,
            self.RoleChoices.INVENTORY,
            self.RoleChoices.FINANCE,
        }

    def __str__(self):
        return f"{self.email} ({self.role})"