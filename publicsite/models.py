from django.db import models
from django.utils.translation import gettext_lazy as _


class HeroSection(models.Model):
    badge_text = models.CharField(_("Badge Text"), max_length=120, default="Discover your next journey")
    logo = models.ImageField(_("Logo"), upload_to="publicsite/logo/", blank=True, null=True)
    image = models.ImageField(_("Image"), upload_to="publicsite/hero/", blank=True, null=True)
    headline = models.CharField(
        _("Headline"),
        max_length=255,
        default="Find Premium Hotels and Curated Tour Experiences in Minutes",
    )
    description = models.TextField(
        _("Description"),
        default=(
            "Jovira helps travelers and agencies discover top-rated stays, unforgettable tours, "
            "and smooth travel services across Turkey."
        ),
    )
    search_placeholder = models.CharField(
        _("Search Placeholder"),
        max_length=255,
        default="Search hotels by location or name",
    )
    search_button_text = models.CharField(_("Search Button Text"), max_length=80, default="Search Now")
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Hero Section")
        verbose_name_plural = _("Hero Section")

    def __str__(self):
        return "Homepage Hero Section"

    def save(self, *args, **kwargs):
        # Keep a single source of truth for the public homepage hero content.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
