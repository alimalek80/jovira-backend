from django.db import models
from django.utils.translation import gettext_lazy as _


class Agency(models.Model):
    name = models.CharField(_("Agency Name"), max_length=255)
    agency_type = models.CharField(_("Agency Type"), max_length=100)
    contact_person = models.CharField(_("Contact Person"), max_length=255)

    email = models.EmailField(_("Email"), max_length=255, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    mobile_phone = models.CharField(_("Mobile Phone"), max_length=50, blank=True, null=True)
    skype_id = models.CharField(_("Skype ID"), max_length=100, blank=True, null=True)
    icq = models.CharField(_("ICQ"), max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _("Agency")
        verbose_name_plural = _("Agencies")
        ordering = ("name",)

    def __str__(self):
        return self.name