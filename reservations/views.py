from django.db.models import F, Q

from rest_framework import permissions, viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied

from accounts.permissions import (
    IsReservationEditorOrReadOnlyIfLocked,
    IsReservationOperationsRole,
    IsReservationWorkflowRole,
    ReadOnlyOrReservationOperationsRole,
)
from inventory.models import HotelRoom

from .models import (
    ExcursionBooking,
    ExcursionService,
    FlightTicket,
    HotelBooking,
    Reservation,
    ReservationActivityLog,
    Tourist,
    TransferService,
)
from .serializers import (
    ExcursionBookingSerializer,
    ExcursionServiceSerializer,
    FlightTicketSerializer,
    HotelBookingSerializer,
    ReservationSerializer,
    TouristSerializer,
    TransferServiceSerializer,
    ReservationActivityLogSerializer,
)


class PreventHardDeleteMixin:
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE",
            detail="Hard deletion is disabled. Please use the cancellation workflow instead.",
        )


def _adjust_availability(hotel_room_id, delta):
    if delta != 0:
        HotelRoom.objects.filter(pk=hotel_room_id).update(
            availability_count=F("availability_count") + delta
        )


def _is_internal_reservation_user(user):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    return user.role in {
        user.RoleChoices.ADMIN,
        user.RoleChoices.SALES,
        user.RoleChoices.RESERVATION,
        user.RoleChoices.FINANCE,
    }


def _empty_q(prefix=""):
    if prefix:
        return Q(**{f"{prefix}pk__isnull": True})
    return Q(pk__isnull=True)


def _reservation_owner_q(user, prefix=""):
    if not user or not user.is_authenticated:
        return _empty_q(prefix)

    if _is_internal_reservation_user(user):
        return Q()

    reservation_field_names = {
        field.name for field in Reservation._meta.get_fields()
    }

    owner_q = Q()
    has_owner_filter = False

    if getattr(user, "role", None) == user.RoleChoices.AGENCY and getattr(user, "agency_id", None):
        if "agency" in reservation_field_names:
            owner_q |= Q(**{f"{prefix}agency_id": user.agency_id})
            has_owner_filter = True

    if "user" in reservation_field_names:
        owner_q |= Q(**{f"{prefix}user_id": user.id})
        has_owner_filter = True

    if "customer" in reservation_field_names:
        owner_q |= Q(**{f"{prefix}customer_id": user.id})
        has_owner_filter = True

    if has_owner_filter:
        return owner_q

    return _empty_q(prefix)


def _filter_by_reservation_access(queryset, request, prefix=""):
    user = request.user

    if not user or not user.is_authenticated:
        return queryset.none()

    if _is_internal_reservation_user(user):
        return queryset

    return queryset.filter(_reservation_owner_q(user, prefix=prefix))


def _ensure_reservation_is_editable_for_request(request, reservation):
    user = request.user

    if not reservation:
        return

    if not getattr(reservation, "is_locked_by_finance", False):
        return

    if user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN:
        return

    raise PermissionDenied(
        "This reservation is locked by finance and cannot be modified by this role."
    )

def _create_reservation_activity_log(request, reservation, action, message="", metadata=None):
    if not reservation:
        return None

    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        user = None

    return ReservationActivityLog.objects.create(
        reservation=reservation,
        actor=user,
        action=action,
        message=message,
        metadata=metadata or {},
    )

def _hotel_booking_log_metadata(booking):
    return {
        "hotel_booking_id": booking.id,
        "hotel_room_id": booking.hotel_room_id,
        "hotel_name": getattr(getattr(booking.hotel_room, "hotel", None), "name", ""),
        "room_type": getattr(booking.hotel_room, "room_type", ""),
        "board_type": getattr(booking.hotel_room, "board_type", ""),
        "check_in_date": str(booking.check_in_date),
        "check_out_date": str(booking.check_out_date),
        "quantity": booking.quantity,
        "status": booking.status,
        "confirm_booking_number": booking.confirm_booking_number,
        "agent_confirmation_number": booking.agent_confirmation_number,
        "hotel_cancellation_number": booking.hotel_cancellation_number,
        "updated_fields": [],
    }

class AdminReservationViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by("-created_at")
    serializer_class = ReservationSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = (IsReservationOperationsRole,)
        else:
            permission_classes = (
                IsReservationWorkflowRole,
                IsReservationEditorOrReadOnlyIfLocked,
            )

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        reservation = serializer.save()

        _create_reservation_activity_log(
            self.request,
            reservation,
            ReservationActivityLog.ActionChoices.CREATED,
            "Reservation was created.",
            {
                "status": reservation.status,
                "agency_id": reservation.agency_id,
                "tour_package_id": reservation.tour_package_id,
            },
        )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        old_is_locked_by_finance = serializer.instance.is_locked_by_finance

        reservation = serializer.save()

        if old_status != reservation.status:
            _create_reservation_activity_log(
                self.request,
                reservation,
                ReservationActivityLog.ActionChoices.STATUS_CHANGED,
                "Reservation status was changed.",
                {
                    "old_status": old_status,
                    "new_status": reservation.status,
                },
            )
            return

        if old_is_locked_by_finance != reservation.is_locked_by_finance:
            action = (
                ReservationActivityLog.ActionChoices.FINANCE_LOCKED
                if reservation.is_locked_by_finance
                else ReservationActivityLog.ActionChoices.FINANCE_UNLOCKED
            )
            message = (
                "Reservation was locked by finance."
                if reservation.is_locked_by_finance
                else "Reservation was unlocked by finance."
            )

            _create_reservation_activity_log(
                self.request,
                reservation,
                action,
                message,
                {
                    "old_is_locked_by_finance": old_is_locked_by_finance,
                    "new_is_locked_by_finance": reservation.is_locked_by_finance,
                },
            )
            return

        _create_reservation_activity_log(
            self.request,
            reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            "Reservation was updated.",
            {
                "updated_fields": list(self.request.data.keys()),
            },
        )

class AdminReservationActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReservationActivityLog.objects.select_related(
        "reservation",
        "actor",
    ).order_by("-created_at")
    serializer_class = ReservationActivityLogSerializer
    permission_classes = (IsReservationWorkflowRole,)

    def get_queryset(self):
        queryset = super().get_queryset()
        reservation_id = self.request.query_params.get("reservation")

        if reservation_id:
            queryset = queryset.filter(reservation_id=reservation_id)

        return queryset


class ClientReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by("-created_at")
    serializer_class = ReservationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return _filter_by_reservation_access(qs, self.request)


class AdminTouristViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = Tourist.objects.select_related("reservation").order_by("id")
    serializer_class = TouristSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class ClientTouristViewSet(viewsets.ModelViewSet):
    queryset = Tourist.objects.select_related("reservation").order_by("id")
    serializer_class = TouristSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return _filter_by_reservation_access(qs, self.request, prefix="reservation__")

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class AdminHotelBookingViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = HotelBooking.objects.select_related(
        "reservation",
        "hotel_room__hotel",
        "selling_currency",
        "cost_currency",
    ).prefetch_related("tourists").order_by("check_in_date")
    serializer_class = HotelBookingSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)

        booking = serializer.save()

        if booking.status != HotelBooking.StatusChoices.CANCELLED:
            _adjust_availability(booking.hotel_room_id, -booking.quantity)

        _create_reservation_activity_log(
            self.request,
            booking.reservation,
            ReservationActivityLog.ActionChoices.HOTEL_BOOKING_ADDED,
            "Hotel booking was added.",
            _hotel_booking_log_metadata(booking),
        )

    def perform_update(self, serializer):
        _ensure_reservation_is_editable_for_request(
            self.request,
            serializer.instance.reservation,
        )

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
                _adjust_availability(
                    booking.hotel_room_id,
                    -(booking.quantity - old_qty),
                )

        action = ReservationActivityLog.ActionChoices.HOTEL_BOOKING_UPDATED
        message = "Hotel booking was updated."

        if old_status != booking.status and booking.status == HotelBooking.StatusChoices.CANCELLED:
            message = "Hotel booking was cancelled."

        metadata = _hotel_booking_log_metadata(booking)
        metadata["old_status"] = old_status
        metadata["new_status"] = booking.status
        metadata["old_quantity"] = old_qty
        metadata["new_quantity"] = booking.quantity
        metadata["old_hotel_room_id"] = old_room_id
        metadata["new_hotel_room_id"] = booking.hotel_room_id
        metadata["updated_fields"] = list(self.request.data.keys())

        _create_reservation_activity_log(
            self.request,
            booking.reservation,
            action,
            message,
            metadata,
        )


class ClientHotelBookingViewSet(viewsets.ModelViewSet):
    queryset = HotelBooking.objects.select_related(
        "reservation",
        "hotel_room__hotel",
        "selling_currency",
        "cost_currency",
    ).prefetch_related("tourists").order_by("check_in_date")
    serializer_class = HotelBookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return _filter_by_reservation_access(qs, self.request, prefix="reservation__")

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)

        booking = serializer.save()

        if booking.status != HotelBooking.StatusChoices.CANCELLED:
            _adjust_availability(booking.hotel_room_id, -booking.quantity)

    def perform_destroy(self, instance):
        if instance.status != HotelBooking.StatusChoices.CANCELLED:
            _adjust_availability(instance.hotel_room_id, +instance.quantity)

        instance.delete()

    def perform_update(self, serializer):
        _ensure_reservation_is_editable_for_request(
            self.request,
            serializer.instance.reservation,
        )

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
                _adjust_availability(
                    booking.hotel_room_id,
                    -(booking.quantity - old_qty),
                )


class AdminFlightTicketViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = FlightTicket.objects.select_related(
        "reservation",
        "flight",
        "tourist",
    ).order_by("id")
    serializer_class = FlightTicketSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class ClientFlightTicketViewSet(viewsets.ModelViewSet):
    queryset = FlightTicket.objects.select_related(
        "reservation",
        "flight",
        "tourist",
    ).order_by("id")
    serializer_class = FlightTicketSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return _filter_by_reservation_access(qs, self.request, prefix="reservation__")

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class AdminExcursionBookingViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = ExcursionBooking.objects.select_related(
        "reservation",
        "excursion",
    ).prefetch_related("tourists").order_by("tour_date")
    serializer_class = ExcursionBookingSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class ClientExcursionBookingViewSet(viewsets.ModelViewSet):
    queryset = ExcursionBooking.objects.select_related(
        "reservation",
        "excursion",
    ).prefetch_related("tourists").order_by("tour_date")
    serializer_class = ExcursionBookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return _filter_by_reservation_access(qs, self.request, prefix="reservation__")

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class AdminTransferServiceViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = TransferService.objects.select_related(
        "reservation",
        "transfer",
        "tour_package",
        "currency",
    ).prefetch_related("passengers").order_by("service_date", "id")
    serializer_class = TransferServiceSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class ClientTransferServiceViewSet(viewsets.ModelViewSet):
    queryset = TransferService.objects.select_related(
        "reservation",
        "transfer",
        "tour_package",
        "currency",
    ).prefetch_related("passengers").order_by("service_date", "id")
    serializer_class = TransferServiceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return _filter_by_reservation_access(qs, self.request, prefix="reservation__")

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        serializer.save()


class AdminExcursionServiceViewSet(PreventHardDeleteMixin, viewsets.ModelViewSet):
    queryset = ExcursionService.objects.select_related(
        "excursion",
        "selling_currency",
        "cost_currency",
    ).order_by("-excursion_date")
    serializer_class = ExcursionServiceSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)


class ClientExcursionServiceViewSet(viewsets.ModelViewSet):
    queryset = ExcursionService.objects.select_related(
        "excursion",
        "selling_currency",
        "cost_currency",
    ).order_by("-excursion_date")
    serializer_class = ExcursionServiceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if _is_internal_reservation_user(user):
            return qs

        return qs.none()