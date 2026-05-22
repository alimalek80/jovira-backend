from rest_framework import permissions, viewsets

from .models import Excursion, Flight, Hotel, TourPackage
from .permissions import IsAdminOrStaffRole
from .serializers import (
	ClientTourPackageSerializer,
	ExcursionSerializer,
	FlightSerializer,
	HotelSerializer,
	TourPackageSerializer,
)


class AdminHotelViewSet(viewsets.ModelViewSet):
	queryset = Hotel.objects.all().order_by("name")
	serializer_class = HotelSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientHotelViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Hotel.objects.all().order_by("name")
	serializer_class = HotelSerializer
	permission_classes = (permissions.AllowAny,)


class AdminFlightViewSet(viewsets.ModelViewSet):
	queryset = Flight.objects.all().order_by("-departure_time")
	serializer_class = FlightSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientFlightViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Flight.objects.all().order_by("-departure_time")
	serializer_class = FlightSerializer
	permission_classes = (permissions.AllowAny,)


class AdminTourPackageViewSet(viewsets.ModelViewSet):
	queryset = TourPackage.objects.all().order_by("name")
	serializer_class = TourPackageSerializer
	permission_classes = (IsAdminOrStaffRole,)


class ClientTourPackageViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TourPackage.objects.all().order_by("name")
	serializer_class = ClientTourPackageSerializer
	permission_classes = (permissions.AllowAny,)


class AdminExcursionViewSet(viewsets.ModelViewSet):
	queryset = Excursion.objects.all().order_by("name")
	serializer_class = ExcursionSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientExcursionViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Excursion.objects.all().order_by("name")
	serializer_class = ExcursionSerializer
	permission_classes = (permissions.AllowAny,)
