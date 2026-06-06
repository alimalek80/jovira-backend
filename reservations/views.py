from rest_framework import permissions, viewsets
from django.db.models import F

from inventory.models import HotelRoom
from .models import ExcursionBooking, ExcursionService, FlightTicket, HotelBooking, Reservation, Tourist, TransferService
from .serializers import (
	ExcursionBookingSerializer,
	ExcursionServiceSerializer,
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


def _adjust_availability(hotel_room_id, delta):
	"""Atomically adjust HotelRoom.availability_count by delta (positive = restore, negative = deduct)."""
	if delta != 0:
		HotelRoom.objects.filter(pk=hotel_room_id).update(
			availability_count=F("availability_count") + delta
		)


class AdminHotelBookingViewSet(viewsets.ModelViewSet):
	queryset = HotelBooking.objects.select_related(
		"hotel_room__hotel", "selling_currency", "cost_currency"
	).order_by("check_in_date")
	serializer_class = HotelBookingSerializer
	permission_classes = (permissions.IsAdminUser,)

	def perform_create(self, serializer):
		booking = serializer.save()
		if booking.status != HotelBooking.StatusChoices.CANCELLED:
			_adjust_availability(booking.hotel_room_id, -booking.quantity)

	def perform_destroy(self, instance):
		if instance.status != HotelBooking.StatusChoices.CANCELLED:
			_adjust_availability(instance.hotel_room_id, +instance.quantity)
		instance.delete()

	def perform_update(self, serializer):
		old_qty = serializer.instance.quantity
		old_status = serializer.instance.status
		old_room_id = serializer.instance.hotel_room_id

		booking = serializer.save()

		was_active = old_status != HotelBooking.StatusChoices.CANCELLED
		is_active = booking.status != HotelBooking.StatusChoices.CANCELLED

		# Room changed — restore old room, deduct new room
		if old_room_id != booking.hotel_room_id:
			if was_active:
				_adjust_availability(old_room_id, +old_qty)
			if is_active:
				_adjust_availability(booking.hotel_room_id, -booking.quantity)
		else:
			if was_active and not is_active:
				# Cancelled — restore
				_adjust_availability(booking.hotel_room_id, +old_qty)
			elif not was_active and is_active:
				# Re-activated — deduct
				_adjust_availability(booking.hotel_room_id, -booking.quantity)
			elif is_active and old_qty != booking.quantity:
				# Quantity changed — adjust difference
				_adjust_availability(booking.hotel_room_id, -(booking.quantity - old_qty))


class ClientHotelBookingViewSet(viewsets.ModelViewSet):
	queryset = HotelBooking.objects.select_related(
		"hotel_room__hotel", "selling_currency", "cost_currency"
	).order_by("check_in_date")
	serializer_class = HotelBookingSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def perform_create(self, serializer):
		booking = serializer.save()
		if booking.status != HotelBooking.StatusChoices.CANCELLED:
			_adjust_availability(booking.hotel_room_id, -booking.quantity)

	def perform_destroy(self, instance):
		if instance.status != HotelBooking.StatusChoices.CANCELLED:
			_adjust_availability(instance.hotel_room_id, +instance.quantity)
		instance.delete()

	def perform_update(self, serializer):
		old_qty = serializer.instance.quantity
		old_status = serializer.instance.status
		old_room_id = serializer.instance.hotel_room_id

		booking = serializer.save()

		was_active = old_status != HotelBooking.StatusChoices.CANCELLED
		is_active = booking.status != HotelBooking.StatusChoices.CANCELLED

		if old_room_id != booking.hotel_room_id:
			if was_active:
				_adjust_availability(old_room_id, +old_qty)
			if is_active:
				_adjust_availability(booking.hotel_room_id, -booking.quantity)
		else:
			if was_active and not is_active:
				_adjust_availability(booking.hotel_room_id, +old_qty)
			elif not was_active and is_active:
				_adjust_availability(booking.hotel_room_id, -booking.quantity)
			elif is_active and old_qty != booking.quantity:
				_adjust_availability(booking.hotel_room_id, -(booking.quantity - old_qty))


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


class AdminExcursionServiceViewSet(viewsets.ModelViewSet):
	queryset = ExcursionService.objects.all().order_by("-excursion_date")
	serializer_class = ExcursionServiceSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientExcursionServiceViewSet(viewsets.ModelViewSet):
	queryset = ExcursionService.objects.all().order_by("-excursion_date")
	serializer_class = ExcursionServiceSerializer
	permission_classes = (permissions.IsAuthenticated,)
