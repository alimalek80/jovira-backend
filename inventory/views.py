from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from .models import Excursion, Flight, Hotel, HotelImage, HotelRoom, TourPackage, Transfer, TransferProvider
from .permissions import IsAdminOrStaffRole
from .serializers import (
	ClientExcursionSerializer,
	ClientFlightSerializer,
	ClientHotelRoomSerializer,
	ClientHotelSerializer,
	ClientTourPackageSerializer,
	ClientTransferSerializer,
	ExcursionSerializer,
	FlightSerializer,
	HotelImageSerializer,
	HotelRoomSerializer,
	HotelSerializer,
	TourPackageSerializer,
	TransferProviderSerializer,
	TransferSerializer,
)


class AdminHotelViewSet(viewsets.ModelViewSet):
	queryset = Hotel.objects.all().order_by("name")
	serializer_class = HotelSerializer
	permission_classes = (permissions.IsAdminUser,)


class AdminHotelRoomViewSet(viewsets.ModelViewSet):
	queryset = HotelRoom.objects.select_related("hotel", "currency").order_by("hotel", "date_from", "room_type")
	serializer_class = HotelRoomSerializer
	permission_classes = (permissions.IsAdminUser,)

	def get_queryset(self):
		qs = super().get_queryset()
		hotel_id = self.request.query_params.get("hotel")
		if hotel_id:
			qs = qs.filter(hotel_id=hotel_id)
		return qs


class AdminHotelImageViewSet(viewsets.ModelViewSet):
	queryset = HotelImage.objects.all().order_by("hotel", "order", "id")
	serializer_class = HotelImageSerializer
	permission_classes = (permissions.IsAdminUser,)
	parser_classes = (MultiPartParser, FormParser)

	def get_queryset(self):
		qs = super().get_queryset()
		hotel_id = self.request.query_params.get("hotel")
		if hotel_id:
			qs = qs.filter(hotel_id=hotel_id)
		return qs


class ClientHotelViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Hotel.objects.all().order_by("name")
	serializer_class = ClientHotelSerializer
	permission_classes = (permissions.AllowAny,)


class ClientHotelRoomViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = HotelRoom.objects.select_related("hotel", "currency").order_by("hotel", "date_from", "room_type")
	serializer_class = ClientHotelRoomSerializer
	permission_classes = (permissions.AllowAny,)

	def get_queryset(self):
		qs = super().get_queryset()
		hotel_id = self.request.query_params.get("hotel")
		if hotel_id:
			qs = qs.filter(hotel_id=hotel_id)
		return qs


class AdminFlightViewSet(viewsets.ModelViewSet):
	queryset = Flight.objects.all().order_by("-departure_time")
	serializer_class = FlightSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientFlightViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Flight.objects.all().order_by("-departure_time")
	serializer_class = ClientFlightSerializer
	permission_classes = (permissions.AllowAny,)


class AdminTourPackageViewSet(viewsets.ModelViewSet):
	queryset = TourPackage.objects.select_related("currency").prefetch_related(
		"flights",
		"hotels",
		"transfers",
		"excursions",
	).order_by("name")
	serializer_class = TourPackageSerializer
	permission_classes = (IsAdminOrStaffRole,)


class ClientTourPackageViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TourPackage.objects.select_related("currency").prefetch_related(
		"flights",
		"hotels",
		"transfers",
		"excursions",
	).order_by("name")
	serializer_class = ClientTourPackageSerializer
	permission_classes = (permissions.AllowAny,)


class AdminExcursionViewSet(viewsets.ModelViewSet):
	queryset = Excursion.objects.all().order_by("name")
	serializer_class = ExcursionSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientExcursionViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Excursion.objects.all().order_by("name")
	serializer_class = ClientExcursionSerializer
	permission_classes = (permissions.AllowAny,)


class AdminTransferProviderViewSet(viewsets.ModelViewSet):
	queryset = TransferProvider.objects.all().order_by("name")
	serializer_class = TransferProviderSerializer
	permission_classes = (permissions.IsAdminUser,)


class AdminTransferViewSet(viewsets.ModelViewSet):
	queryset = Transfer.objects.select_related("provider").order_by("name")
	serializer_class = TransferSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientTransferViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Transfer.objects.select_related("provider").order_by("name")
	serializer_class = ClientTransferSerializer
	permission_classes = (permissions.IsAuthenticated,)
