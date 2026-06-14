from decimal import Decimal, InvalidOperation

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFinanceRole

from .models import Currency, ExchangeRate, Invoice
from .serializers import CurrencySerializer, ExchangeRateSerializer, InvoiceSerializer
from .utils import convert_amount


class AdminCurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all().order_by("code")
    serializer_class = CurrencySerializer
    permission_classes = (IsFinanceRole,)


class ClientCurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Currency.objects.filter(is_active=True).order_by("code")
    serializer_class = CurrencySerializer
    permission_classes = (permissions.AllowAny,)


class AdminExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.all().order_by("-last_updated")
    serializer_class = ExchangeRateSerializer
    permission_classes = (IsFinanceRole,)


class ClientExchangeRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExchangeRate.objects.all().order_by("-last_updated")
    serializer_class = ExchangeRateSerializer
    permission_classes = (permissions.AllowAny,)


class AdminInvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related(
        "reservation",
        "reservation__agency",
    ).order_by("-id")
    serializer_class = InvoiceSerializer
    permission_classes = (IsFinanceRole,)


class ClientInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        qs = Invoice.objects.select_related(
            "reservation",
            "reservation__agency",
        ).order_by("-id")

        if user.is_superuser or user.is_staff or user.role in {
            user.RoleChoices.ADMIN,
            user.RoleChoices.FINANCE,
        }:
            return qs

        if user.role == user.RoleChoices.AGENCY and getattr(user, "agency_id", None):
            return qs.filter(reservation__agency_id=user.agency_id)

        return qs.none()


class ClientCurrencyConvertView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        from_code = (request.query_params.get("from") or "").upper()
        to_code = (request.query_params.get("to") or "").upper()
        amount_raw = request.query_params.get("amount")

        if not from_code or not to_code or amount_raw is None:
            return Response(
                {"detail": "Query params 'from', 'to', and 'amount' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(amount_raw))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"detail": "Invalid amount value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from_currency = Currency.objects.filter(
            code=from_code,
            is_active=True,
        ).first()
        to_currency = Currency.objects.filter(
            code=to_code,
            is_active=True,
        ).first()

        if from_currency is None or to_currency is None:
            return Response(
                {"detail": "Both source and target currencies must exist and be active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            converted = convert_amount(amount, from_currency.id, to_currency.id)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        effective_rate = (
            Decimal("0")
            if amount == 0
            else (converted / amount).quantize(Decimal("0.0000000001"))
        )

        return Response(
            {
                "from": from_code,
                "to": to_code,
                "amount": str(amount),
                "converted_amount": str(converted),
                "effective_rate": str(effective_rate),
            }
        )