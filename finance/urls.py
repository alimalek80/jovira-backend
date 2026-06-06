from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminCurrencyViewSet,
    AdminExchangeRateViewSet,
    AdminInvoiceViewSet,
    ClientCurrencyViewSet,
    ClientCurrencyConvertView,
    ClientExchangeRateViewSet,
    ClientInvoiceViewSet,
)

admin_router = DefaultRouter()
admin_router.register(r"currencies", AdminCurrencyViewSet, basename="admin-currencies")
admin_router.register(r"exchange-rates", AdminExchangeRateViewSet, basename="admin-exchange-rates")
admin_router.register(r"invoices", AdminInvoiceViewSet, basename="admin-invoices")

client_router = DefaultRouter()
client_router.register(r"currencies", ClientCurrencyViewSet, basename="client-currencies")
client_router.register(r"exchange-rates", ClientExchangeRateViewSet, basename="client-exchange-rates")
client_router.register(r"invoices", ClientInvoiceViewSet, basename="client-invoices")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("client/", include(client_router.urls)),
    path("client/convert/", ClientCurrencyConvertView.as_view(), name="client-currency-convert"),
]
