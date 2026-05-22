from rest_framework import permissions, viewsets

from .models import ExcursionBooking, FlightTicket, HotelBooking, Reservation, Tourist, TransferService
from .serializers import (
	ExcursionBookingSerializer,
	FlightTicketSerializer,
	HotelBookingSerializer,
	ReservationSerializer,
	TouristSerializer,
	TransferServiceSerializer,
)


class AdminReservationViewSet(viewsets.ModelViewSet):
	queryset = Reservation.objects.all().order_by("-created_at")
	serializer_class = ReservationSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientReservationViewSet(viewsets.ModelViewSet):
	queryset = Reservation.objects.all().order_by("-created_at")
	serializer_class = ReservationSerializer
	permission_classes = (permissions.IsAuthenticated,)


class AdminTouristViewSet(viewsets.ModelViewSet):
	queryset = Tourist.objects.all().order_by("id")
	serializer_class = TouristSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientTouristViewSet(viewsets.ModelViewSet):
	queryset = Tourist.objects.all().order_by("id")
	serializer_class = TouristSerializer
	permission_classes = (permissions.IsAuthenticated,)


class AdminHotelBookingViewSet(viewsets.ModelViewSet):
	queryset = HotelBooking.objects.all().order_by("check_in_date")
	serializer_class = HotelBookingSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientHotelBookingViewSet(viewsets.ModelViewSet):
	queryset = HotelBooking.objects.all().order_by("check_in_date")
	serializer_class = HotelBookingSerializer
	permission_classes = (permissions.IsAuthenticated,)


class AdminFlightTicketViewSet(viewsets.ModelViewSet):
	queryset = FlightTicket.objects.all().order_by("id")
	serializer_class = FlightTicketSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientFlightTicketViewSet(viewsets.ModelViewSet):
	queryset = FlightTicket.objects.all().order_by("id")
	serializer_class = FlightTicketSerializer
	permission_classes = (permissions.IsAuthenticated,)


class AdminExcursionBookingViewSet(viewsets.ModelViewSet):
	queryset = ExcursionBooking.objects.all().order_by("tour_date")
	serializer_class = ExcursionBookingSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientExcursionBookingViewSet(viewsets.ModelViewSet):
	queryset = ExcursionBooking.objects.all().order_by("tour_date")
	serializer_class = ExcursionBookingSerializer
	permission_classes = (permissions.IsAuthenticated,)


class AdminTransferServiceViewSet(viewsets.ModelViewSet):
	queryset = TransferService.objects.all().order_by("service_date", "id")
	serializer_class = TransferServiceSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientTransferServiceViewSet(viewsets.ModelViewSet):
	queryset = TransferService.objects.all().order_by("service_date", "id")
	serializer_class = TransferServiceSerializer
	permission_classes = (permissions.IsAuthenticated,)
