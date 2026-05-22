from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand

from finance.models import Currency, ExchangeRate


class Command(BaseCommand):
    help = "Fetch daily EUR-based exchange rates from Frankfurter and update ExchangeRate records."

    def handle(self, *args, **options):
        eur_currency = Currency.objects.filter(code="EUR", is_active=True).first()
        if eur_currency is None:
            self.stdout.write(self.style.WARNING("EUR currency is missing or inactive. No rates updated."))
            return

        url = "https://api.frankfurter.app/latest?from=EUR"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("rates", {})

        updated_count = 0

        active_currencies = Currency.objects.filter(is_active=True).exclude(code="EUR")
        for currency in active_currencies:
            raw_rate = rates.get(currency.code)
            if raw_rate is None:
                continue

            try:
                rate_value = Decimal(str(raw_rate))
            except (InvalidOperation, TypeError, ValueError):
                continue

            ExchangeRate.objects.update_or_create(
                base_currency=eur_currency,
                target_currency=currency,
                defaults={"rate": rate_value},
            )
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully fetched and updated {updated_count} exchange rate(s) from Frankfurter."
            )
        )