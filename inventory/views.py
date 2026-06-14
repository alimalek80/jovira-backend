from django.db.models import Q, Sum

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from accounts.permissions import IsInventoryRole

from .models import (
    Excursion,
    Flight,
    Hotel,
    HotelImage,
    HotelRoom,
    TourPackage,
    Transfer,
    TransferProvider,
)
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
    permission_classes = (IsInventoryRole,)


class AdminHotelRoomViewSet(viewsets.ModelViewSet):
    queryset = HotelRoom.objects.select_related("hotel", "currency").order_by(
        "hotel",
        "date_from",
        "room_type",
    )
    serializer_class = HotelRoomSerializer
    permission_classes = (IsInventoryRole,)

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel")

        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)

        return qs

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        """
        Return remaining available rooms split by status for a given date range.

        Query params: check_in (YYYY-MM-DD), check_out (YYYY-MM-DD)
        """
        room = self.get_object()
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")

        if not check_in or not check_out:
            return Response(
                {"detail": "check_in and check_out query parameters are required."},
                status=400,
            )

        from reservations.models import HotelBooking

        overlapping = HotelBooking.objects.filter(
            ~Q(status=HotelBooking.StatusChoices.CANCELLED),
            hotel_room=room,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
        )

        pending_qty = (
            overlapping.filter(status=HotelBooking.StatusChoices.PENDING)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        confirmed_qty = (
            overlapping.filter(status=HotelBooking.StatusChoices.CONFIRMED)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        booked_qty = pending_qty + confirmed_qty

        return Response(
            {
                "hotel_room": room.pk,
                "check_in": check_in,
                "check_out": check_out,
                "total_count": room.availability_count,
                "confirmed_count": confirmed_qty,
                "pending_count": pending_qty,
                "booked_count": booked_qty,
                "available_count": max(0, room.availability_count - booked_qty),
            }
        )


class AdminHotelImageViewSet(viewsets.ModelViewSet):
    queryset = HotelImage.objects.all().order_by("hotel", "order", "id")
    serializer_class = HotelImageSerializer
    permission_classes = (IsInventoryRole,)
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
    queryset = HotelRoom.objects.select_related("hotel", "currency").order_by(
        "hotel",
        "date_from",
        "room_type",
    )
    serializer_class = ClientHotelRoomSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel")

        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)

        return qs

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        """
        Return remaining available rooms split by status for a given date range.

        Query params: check_in (YYYY-MM-DD), check_out (YYYY-MM-DD)
        """
        room = self.get_object()
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")

        if not check_in or not check_out:
            return Response(
                {"detail": "check_in and check_out query parameters are required."},
                status=400,
            )

        from reservations.models import HotelBooking

        overlapping = HotelBooking.objects.filter(
            ~Q(status=HotelBooking.StatusChoices.CANCELLED),
            hotel_room=room,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
        )

        pending_qty = (
            overlapping.filter(status=HotelBooking.StatusChoices.PENDING)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        confirmed_qty = (
            overlapping.filter(status=HotelBooking.StatusChoices.CONFIRMED)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        booked_qty = pending_qty + confirmed_qty

        return Response(
            {
                "hotel_room": room.pk,
                "check_in": check_in,
                "check_out": check_out,
                "total_count": room.availability_count,
                "confirmed_count": confirmed_qty,
                "pending_count": pending_qty,
                "booked_count": booked_qty,
                "available_count": max(0, room.availability_count - booked_qty),
            }
        )


class AdminFlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all().order_by("-departure_time")
    serializer_class = FlightSerializer
    permission_classes = (IsInventoryRole,)


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
    permission_classes = (IsInventoryRole,)

    @action(detail=True, methods=["get"], url_path="hotels")
    def hotels(self, request, pk=None):
        tour_package = self.get_object()
        hotels = tour_package.hotels.all()
        serializer = HotelSerializer(
            hotels,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class ClientTourPackageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TourPackage.objects.select_related("currency").prefetch_related(
        "flights",
        "hotels",
        "transfers",
        "excursions",
    ).order_by("name")
    serializer_class = ClientTourPackageSerializer
    permission_classes = (permissions.AllowAny,)

    @action(detail=True, methods=["get"], url_path="hotels")
    def hotels(self, request, pk=None):
        tour_package = self.get_object()
        hotels = tour_package.hotels.all()
        serializer = ClientHotelSerializer(
            hotels,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class AdminExcursionViewSet(viewsets.ModelViewSet):
    queryset = Excursion.objects.all().order_by("name")
    serializer_class = ExcursionSerializer
    permission_classes = (IsInventoryRole,)


class ClientExcursionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Excursion.objects.all().order_by("name")
    serializer_class = ClientExcursionSerializer
    permission_classes = (permissions.AllowAny,)


class AdminTransferProviderViewSet(viewsets.ModelViewSet):
    queryset = TransferProvider.objects.all().order_by("name")
    serializer_class = TransferProviderSerializer
    permission_classes = (IsInventoryRole,)


class AdminTransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.select_related("provider").order_by("name")
    serializer_class = TransferSerializer
    permission_classes = (IsInventoryRole,)


class ClientTransferViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transfer.objects.select_related("provider").order_by("name")
    serializer_class = ClientTransferSerializer
    permission_classes = (permissions.IsAuthenticated,)