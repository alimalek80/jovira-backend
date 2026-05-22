from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

class CustomUser(AbstractUser):
    class RoleChoices(models.TextChoices):
        NORMAL = "NORMAL", _("Normal User")
        AGENCY = "AGENCY", _("Agency")
        STAFF = "STAFF", _("Staff")

    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("id",)

    @property
    def can_access_agency_prices(self):
        if self.is_superuser or self.is_staff:
            return True
        return self.role in {self.RoleChoices.AGENCY, self.RoleChoices.STAFF}

    def __str__(self):
        return self.email