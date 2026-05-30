from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminExcursionViewSet,
    AdminFlightViewSet,
    AdminHotelImageViewSet,
    AdminHotelViewSet,
    AdminTourPackageViewSet,
    AdminTransferProviderViewSet,
    AdminTransferViewSet,
    ClientExcursionViewSet,
    ClientFlightViewSet,
    ClientHotelViewSet,
    ClientTourPackageViewSet,
    ClientTransferViewSet,
)

admin_router = DefaultRouter()
admin_router.register(r"hotels", AdminHotelViewSet, basename="admin-hotels")
admin_router.register(r"hotel-images", AdminHotelImageViewSet, basename="admin-hotel-images")
admin_router.register(r"flights", AdminFlightViewSet, basename="admin-flights")
admin_router.register(r"tour-packages", AdminTourPackageViewSet, basename="admin-tour-packages")
admin_router.register(r"excursions", AdminExcursionViewSet, basename="admin-excursions")
admin_router.register(r"transfer-providers", AdminTransferProviderViewSet, basename="admin-transfer-providers")
admin_router.register(r"transfers", AdminTransferViewSet, basename="admin-transfers")

client_router = DefaultRouter()
client_router.register(r"hotels", ClientHotelViewSet, basename="client-hotels")
client_router.register(r"flights", ClientFlightViewSet, basename="client-flights")
client_router.register(r"tour-packages", ClientTourPackageViewSet, basename="client-tour-packages")
client_router.register(r"excursions", ClientExcursionViewSet, basename="client-excursions")
client_router.register(r"transfers", ClientTransferViewSet, basename="client-transfers")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("client/", include(client_router.urls)),
]
