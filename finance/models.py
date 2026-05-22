from django.db import models
from django.utils.translation import gettext_lazy as _

from reservations.models import Reservation


class Currency(models.Model):
    code = models.CharField(_("Code"), max_length=3, unique=True)
    name = models.CharField(_("Name"), max_length=50)
    symbol = models.CharField(_("Symbol"), max_length=5)
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} ({self.symbol})"


class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="base_rates",
        verbose_name=_("Base Currency"),
    )
    target_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="target_rates",
        verbose_name=_("Target Currency"),
    )
    rate = models.DecimalField(_("Rate"), max_digits=10, decimal_places=4)
    last_updated = models.DateTimeField(_("Last Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Exchange Rate")
        verbose_name_plural = _("Exchange Rates")
        ordering = ("-last_updated",)
        constraints = [
            models.UniqueConstraint(
                fields=("base_currency", "target_currency"),
                name="unique_exchange_rate_pair",
            )
        ]

    def __str__(self):
        return f"{self.base_currency.code} -> {self.target_currency.code}"


class Invoice(models.Model):
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name="invoice",
        verbose_name=_("Reservation"),
    )
    net_amount = models.DecimalField(_("Net Amount"), max_digits=12, decimal_places=2)
    sale_amount = models.DecimalField(_("Sale Amount"), max_digits=12, decimal_places=2)
    profit = models.DecimalField(_("Profit"), max_digits=12, decimal_places=2)
    agency_commission = models.DecimalField(_("Agency Commission"), max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(_("Is Paid"), default=False)

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ("id",)

    def __str__(self):
        return f"Invoice for {self.reservation.reservation_number}"