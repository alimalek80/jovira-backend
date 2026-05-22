from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminExcursionViewSet,
    AdminFlightViewSet,
    AdminHotelViewSet,
    AdminTourPackageViewSet,
    ClientExcursionViewSet,
    ClientFlightViewSet,
    ClientHotelViewSet,
    ClientTourPackageViewSet,
)

admin_router = DefaultRouter()
admin_router.register(r"hotels", AdminHotelViewSet, basename="admin-hotels")
admin_router.register(r"flights", AdminFlightViewSet, basename="admin-flights")
admin_router.register(r"tour-packages", AdminTourPackageViewSet, basename="admin-tour-packages")
admin_router.register(r"excursions", AdminExcursionViewSet, basename="admin-excursions")

client_router = DefaultRouter()
client_router.register(r"hotels", ClientHotelViewSet, basename="client-hotels")
client_router.register(r"flights", ClientFlightViewSet, basename="client-flights")
client_router.register(r"tour-packages", ClientTourPackageViewSet, basename="client-tour-packages")
client_router.register(r"excursions", ClientExcursionViewSet, basename="client-excursions")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("client/", include(client_router.urls)),
]
