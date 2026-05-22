from rest_framework import permissions, viewsets

from .models import Currency, ExchangeRate, Invoice
from .serializers import CurrencySerializer, ExchangeRateSerializer, InvoiceSerializer


class AdminCurrencyViewSet(viewsets.ModelViewSet):
	queryset = Currency.objects.all().order_by("code")
	serializer_class = CurrencySerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientCurrencyViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Currency.objects.filter(is_active=True).order_by("code")
	serializer_class = CurrencySerializer
	permission_classes = (permissions.AllowAny,)


class AdminExchangeRateViewSet(viewsets.ModelViewSet):
	queryset = ExchangeRate.objects.all().order_by("-last_updated")
	serializer_class = ExchangeRateSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientExchangeRateViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ExchangeRate.objects.all().order_by("-last_updated")
	serializer_class = ExchangeRateSerializer
	permission_classes = (permissions.AllowAny,)


class AdminInvoiceViewSet(viewsets.ModelViewSet):
	queryset = Invoice.objects.all().order_by("id")
	serializer_class = InvoiceSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Invoice.objects.all().order_by("id")
	serializer_class = InvoiceSerializer
	permission_classes = (permissions.IsAuthenticated,)
