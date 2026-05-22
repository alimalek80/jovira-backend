from rest_framework import serializers

from .models import Currency, ExchangeRate, Invoice


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ("id", "code", "name", "name_en", "name_tr", "name_ru", "symbol", "is_active")
        read_only_fields = ("id",)


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ("id", "base_currency", "target_currency", "rate", "last_updated")
        read_only_fields = ("id", "last_updated")


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = (
            "id",
            "reservation",
            "net_amount",
            "sale_amount",
            "profit",
            "agency_commission",
            "is_paid",
        )
        read_only_fields = ("id",)
