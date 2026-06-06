from decimal import Decimal

from django.apps import apps


def convert_amount(amount, from_currency_id, to_currency_id):
    """Convert amount between currencies using stored exchange rates.

    Resolution order:
    1) direct pair (from -> to)
    2) inverse pair (to -> from)
    3) EUR pivot using rates fetched from Frankfurter (EUR -> X)
    """
    value = Decimal(str(amount or "0"))

    if not from_currency_id or not to_currency_id or from_currency_id == to_currency_id:
        return value

    ExchangeRate = apps.get_model("finance", "ExchangeRate")
    Currency = apps.get_model("finance", "Currency")

    direct_rate = (
        ExchangeRate.objects.filter(
            base_currency_id=from_currency_id,
            target_currency_id=to_currency_id,
        )
        .values_list("rate", flat=True)
        .first()
    )
    if direct_rate is not None:
        return (value * Decimal(str(direct_rate))).quantize(Decimal("0.01"))

    inverse_rate = (
        ExchangeRate.objects.filter(
            base_currency_id=to_currency_id,
            target_currency_id=from_currency_id,
        )
        .values_list("rate", flat=True)
        .first()
    )
    if inverse_rate is not None:
        return (value / Decimal(str(inverse_rate))).quantize(Decimal("0.01"))

    eur_id = Currency.objects.filter(code="EUR", is_active=True).values_list("id", flat=True).first()
    if eur_id is None:
        raise ValueError("EUR currency is missing or inactive.")

    if from_currency_id == eur_id:
        amount_in_eur = value
    else:
        eur_to_from = (
            ExchangeRate.objects.filter(
                base_currency_id=eur_id,
                target_currency_id=from_currency_id,
            )
            .values_list("rate", flat=True)
            .first()
        )
        if eur_to_from is None:
            raise ValueError("Missing exchange rate from EUR to source currency.")
        amount_in_eur = value / Decimal(str(eur_to_from))

    if to_currency_id == eur_id:
        return amount_in_eur.quantize(Decimal("0.01"))

    eur_to_target = (
        ExchangeRate.objects.filter(
            base_currency_id=eur_id,
            target_currency_id=to_currency_id,
        )
        .values_list("rate", flat=True)
        .first()
    )
    if eur_to_target is None:
        raise ValueError("Missing exchange rate from EUR to target currency.")

    return (amount_in_eur * Decimal(str(eur_to_target))).quantize(Decimal("0.01"))
