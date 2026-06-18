from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminExcursionBookingViewSet,
    AdminExcursionServiceViewSet,
    AdminFlightTicketViewSet,
    AdminHotelBookingViewSet,
    AdminReservationViewSet,
    AdminTransferServiceViewSet,
    AdminTouristViewSet,
    ClientExcursionBookingViewSet,
    ClientExcursionServiceViewSet,
    ClientFlightTicketViewSet,
    ClientHotelBookingViewSet,
    ClientReservationViewSet,
    ClientTransferServiceViewSet,
    ClientTouristViewSet,
    AdminReservationActivityLogViewSet,
)

admin_router = DefaultRouter()
admin_router.register(r"reservations", AdminReservationViewSet, basename="admin-reservations")
admin_router.register(r"tourists", AdminTouristViewSet, basename="admin-tourists")
admin_router.register(r"hotel-bookings", AdminHotelBookingViewSet, basename="admin-hotel-bookings")
admin_router.register(r"flight-tickets", AdminFlightTicketViewSet, basename="admin-flight-tickets")
admin_router.register(r"excursion-bookings", AdminExcursionBookingViewSet, basename="admin-excursion-bookings")
admin_router.register(r"transfer-services", AdminTransferServiceViewSet, basename="admin-transfer-services")
admin_router.register(r"excursion-services", AdminExcursionServiceViewSet, basename="admin-excursion-services")
admin_router.register(
    r"reservation-activity-logs",
    AdminReservationActivityLogViewSet,
    basename="admin-reservation-activity-logs",
)

client_router = DefaultRouter()
client_router.register(r"reservations", ClientReservationViewSet, basename="client-reservations")
client_router.register(r"tourists", ClientTouristViewSet, basename="client-tourists")
client_router.register(r"hotel-bookings", ClientHotelBookingViewSet, basename="client-hotel-bookings")
client_router.register(r"flight-tickets", ClientFlightTicketViewSet, basename="client-flight-tickets")
client_router.register(r"excursion-bookings", ClientExcursionBookingViewSet, basename="client-excursion-bookings")
client_router.register(r"transfer-services", ClientTransferServiceViewSet, basename="client-transfer-services")
client_router.register(r"excursion-services", ClientExcursionServiceViewSet, basename="client-excursion-services")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("client/", include(client_router.urls)),
]
