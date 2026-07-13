from django.db.models import F, Q

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response

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
    OtherService,
)
from .serializers import (
    ExcursionBookingSerializer,
    ExcursionServiceSerializer,
    FlightTicketSerializer,
    OtherServiceSerializer,
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

    is_locked_by_finance = getattr(reservation, "is_locked_by_finance", False)
    is_confirmed = getattr(reservation, "status", None) == Reservation.StatusChoices.CONFIRMED

    if not is_locked_by_finance and not is_confirmed:
        return

    if user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN:
        return

    if is_confirmed:
        raise PermissionDenied(
            "This reservation is confirmed and cannot be modified by this role."
        )

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

def _flight_ticket_log_metadata(ticket, updated_fields=None):
    return {
        "flight_ticket_id": ticket.id,
        "flight_id": ticket.flight_id,
        "flight_number": getattr(ticket.flight, "flight_number", ""),
        "tourist_id": ticket.tourist_id,
        "tourist_name": str(ticket.tourist) if ticket.tourist_id else "",
        "ticket_number": ticket.ticket_number,
        "pnr_code": ticket.pnr_code,
        "updated_fields": updated_fields or [],
    }

def _transfer_service_log_metadata(service, updated_fields=None):
    return {
        "transfer_service_id": service.id,
        "transfer_id": service.transfer_id,
        "tour_package_id": service.tour_package_id,
        "service_name": service.service_name,
        "service_date": str(service.service_date),
        "on_arrival": service.on_arrival,
        "on_departure": service.on_departure,
        "from_location_type": service.from_location_type,
        "from_location_name": service.from_location_name,
        "to_location_type": service.to_location_type,
        "to_location_name": service.to_location_name,
        "price": str(service.price),
        "agency_price": str(service.agency_price) if service.agency_price is not None else None,
        "currency_id": service.currency_id,
        "updated_fields": updated_fields or [],
    }

def _excursion_booking_log_metadata(booking, updated_fields=None):
    return {
        "excursion_booking_id": booking.id,
        "excursion_id": booking.excursion_id,
        "excursion_name": getattr(booking.excursion, "name", ""),
        "tour_date": str(booking.tour_date),
        "pickup_time": str(booking.pickup_time) if booking.pickup_time else None,
        "tourist_ids": list(booking.tourists.values_list("id", flat=True)),
        "updated_fields": updated_fields or [],
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

    @action(detail=False, methods=["get"], url_path="work-desk")
    def work_desk(self, request):
        queryset = self.get_queryset().filter(
            status__in=[
                Reservation.StatusChoices.DRAFT,
                Reservation.StatusChoices.ON_PROCESS,
            ]
        )

        category = request.query_params.get("category", "active_reservations")
        reservation_number = request.query_params.get("reservation_number")
        rf_number = request.query_params.get("rf_number")
        status_value = request.query_params.get("status")
        agency_id = request.query_params.get("agency")
        tour_package_id = request.query_params.get("tour_package")
        is_locked_by_finance = request.query_params.get("is_locked_by_finance")
        only_me = request.query_params.get("only_me")

        search_number = reservation_number or rf_number

        normalized_category = category.strip().lower()

        empty_placeholder_categories = {
            "pins",
            "reminders",
            "received_requests",
            "sent_requests",
        }

        if normalized_category in empty_placeholder_categories:
            queryset = queryset.none()

        if normalized_category not in {
            "active_reservations",
            *empty_placeholder_categories,
        }:
            queryset = queryset.none()

        if search_number:
            queryset = queryset.filter(
                reservation_number__icontains=search_number
            )

        if status_value:
            queryset = queryset.filter(status=status_value)

        if agency_id:
            queryset = queryset.filter(agency_id=agency_id)

        if tour_package_id:
            queryset = queryset.filter(tour_package_id=tour_package_id)

        if is_locked_by_finance is not None:
            normalized_locked_value = is_locked_by_finance.strip().lower()

            if normalized_locked_value in {"true", "1", "yes"}:
                queryset = queryset.filter(is_locked_by_finance=True)

            if normalized_locked_value in {"false", "0", "no"}:
                queryset = queryset.filter(is_locked_by_finance=False)

        if only_me is not None:
            normalized_only_me_value = only_me.strip().lower()

            if normalized_only_me_value in {"true", "1", "yes"}:
                queryset = queryset.filter(assigned_to=request.user)

            if normalized_only_me_value in {"false", "0", "no"}:
                queryset = queryset.exclude(assigned_to=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    
    @action(detail=True, methods=["post"], url_path="take")
    def take(self, request, pk=None):
        reservation = self.get_object()
        user = request.user

        is_admin = user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN

        if reservation.assigned_to_id and reservation.assigned_to_id != user.id and not is_admin:
            raise PermissionDenied(
                "This reservation is already assigned to another user."
            )

        old_assigned_to_id = reservation.assigned_to_id

        reservation.assigned_to = user
        reservation.save(update_fields=["assigned_to"])

        _create_reservation_activity_log(
            request,
            reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            "Reservation was taken by a staff member.",
            {
                "old_assigned_to_id": old_assigned_to_id,
                "new_assigned_to_id": user.id,
                "new_assigned_to_email": user.email,
            },
        )

        serializer = self.get_serializer(reservation)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        reservation = self.get_object()
        user = request.user

        is_admin = user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN
        is_reservation_staff = user.role == user.RoleChoices.RESERVATION

        if not (is_admin or is_reservation_staff):
            raise PermissionDenied(
                "Only ADMIN or RESERVATION roles can confirm a reservation."
            )

        old_status = reservation.status

        reservation.status = Reservation.StatusChoices.CONFIRMED
        reservation.save(update_fields=["status"])

        _create_reservation_activity_log(
            request,
            reservation,
            ReservationActivityLog.ActionChoices.STATUS_CHANGED,
            "Reservation was confirmed.",
            {
                "old_status": old_status,
                "new_status": reservation.status,
            },
        )

        serializer = self.get_serializer(reservation)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"], url_path="financial-summary")
    def financial_summary(self, request, pk=None):
        reservation = self.get_object()

        from decimal import Decimal, InvalidOperation
        from collections import defaultdict

        def to_decimal(value):
            try:
                return Decimal(str(value)) if value is not None else Decimal("0")
            except (InvalidOperation, TypeError):
                return Decimal("0")

        def get_currency_code(currency_fk):
            if currency_fk is None:
                return None
            return getattr(currency_fk, "code", None) or getattr(currency_fk, "iso_code", None) or str(currency_fk.id)

        # selling[currency_code] = total selling amount
        # cost[currency_code] = total cost amount
        selling = defaultdict(Decimal)
        cost = defaultdict(Decimal)

        # Hotel bookings
        for booking in reservation.hotel_bookings.select_related("selling_currency", "cost_currency").all():
            if booking.status == HotelBooking.StatusChoices.CANCELLED:
                continue
            sel_cur = get_currency_code(booking.selling_currency)
            cost_cur = get_currency_code(booking.cost_currency)
            if sel_cur and booking.price:
                selling[sel_cur] += to_decimal(booking.price) * booking.quantity
            if cost_cur and booking.cost:
                cost[cost_cur] += to_decimal(booking.cost) * booking.quantity

        # Transfer services
        for service in reservation.transfer_services.select_related("currency", "cost_currency").all():
            sel_cur = get_currency_code(service.currency)
            cost_cur = get_currency_code(service.cost_currency)
            if sel_cur and service.price:
                selling[sel_cur] += to_decimal(service.price)
            if cost_cur and service.cost:
                cost[cost_cur] += to_decimal(service.cost)

        # Flight tickets
        for ticket in reservation.flight_tickets.select_related("currency", "cost_currency").all():
            sel_cur = get_currency_code(ticket.currency)
            cost_cur = get_currency_code(ticket.cost_currency)
            if sel_cur and ticket.price:
                selling[sel_cur] += to_decimal(ticket.price)
            if cost_cur and ticket.cost:
                cost[cost_cur] += to_decimal(ticket.cost)

        # Other services
        for service in reservation.other_services.select_related("selling_currency", "cost_currency").all():
            sel_cur = get_currency_code(service.selling_currency)
            cost_cur = get_currency_code(service.cost_currency)
            if sel_cur and service.price:
                selling[sel_cur] += to_decimal(service.price)
            if cost_cur and service.cost:
                cost[cost_cur] += to_decimal(service.cost)

        # Build per-currency breakdown with margin
        all_currencies = set(selling.keys()) | set(cost.keys())
        breakdown = []
        for currency in sorted(all_currencies):
            sel = selling.get(currency, Decimal("0"))
            cst = cost.get(currency, Decimal("0"))
            breakdown.append({
                "currency": currency,
                "total_selling": str(sel.quantize(Decimal("0.01"))),
                "total_cost": str(cst.quantize(Decimal("0.01"))),
                "margin": str((sel - cst).quantize(Decimal("0.01"))),
            })

        return Response({
            "reservation_id": reservation.id,
            "reservation_number": reservation.reservation_number,
            "breakdown": breakdown,
        })
    
    @action(detail=True, methods=["post"], url_path="ping-pong")
    def ping_pong(self, request, pk=None):
        reservation = self.get_object()
        user = request.user

        is_admin = user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN
        is_finance = user.role == user.RoleChoices.FINANCE
        is_reservation = user.role == user.RoleChoices.RESERVATION

        # Only ADMIN, FINANCE, and RESERVATION roles can use this action.
        if not (is_admin or is_finance or is_reservation):
            raise PermissionDenied(
                "Only ADMIN, FINANCE, or RESERVATION roles can use the Ping-Pong action."
            )

        # Determine direction:
        # - RESERVATION staff sends TO finance (ping): locks the reservation
        # - FINANCE or ADMIN sends BACK to reservation (pong): unlocks it
        direction = request.data.get("direction", "ping")

        if direction == "ping":
            # Only RESERVATION or ADMIN can ping (send to finance)
            if not (is_reservation or is_admin):
                raise PermissionDenied(
                    "Only RESERVATION or ADMIN roles can send to Finance."
                )
            if reservation.is_locked_by_finance:
                return Response(
                    {"detail": "This reservation is already with Finance."},
                    status=400,
                )
            reservation.is_locked_by_finance = True
            reservation.save(update_fields=["is_locked_by_finance"])
            message = "Reservation was sent to Finance (Ping)."
            action_choice = ReservationActivityLog.ActionChoices.FINANCE_LOCKED

        elif direction == "pong":
            # Only FINANCE or ADMIN can pong (send back to reservation)
            if not (is_finance or is_admin):
                raise PermissionDenied(
                    "Only FINANCE or ADMIN roles can send back to Reservation."
                )
            if not reservation.is_locked_by_finance:
                return Response(
                    {"detail": "This reservation is not currently with Finance."},
                    status=400,
                )
            reservation.is_locked_by_finance = False
            reservation.save(update_fields=["is_locked_by_finance"])
            message = "Reservation was returned to Reservation team (Pong)."
            action_choice = ReservationActivityLog.ActionChoices.FINANCE_UNLOCKED

        else:
            return Response(
                {"detail": "Invalid direction. Use 'ping' or 'pong'."},
                status=400,
            )

        _create_reservation_activity_log(
            request,
            reservation,
            action_choice,
            message,
            {
                "direction": direction,
                "triggered_by": user.email,
                "is_locked_by_finance": reservation.is_locked_by_finance,
            },
        )

        serializer = self.get_serializer(reservation)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="finance-queue")
    def finance_queue(self, request):
        user = request.user

        is_admin = user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN
        is_finance = user.role == user.RoleChoices.FINANCE

        if not (is_admin or is_finance):
            raise PermissionDenied(
                "Only ADMIN or FINANCE roles can access the finance queue."
            )

        queryset = self.get_queryset().filter(is_locked_by_finance=True)

        reservation_number = request.query_params.get("reservation_number")
        agency_id = request.query_params.get("agency")
        status_value = request.query_params.get("status")

        if reservation_number:
            queryset = queryset.filter(
                reservation_number__icontains=reservation_number
            )

        if agency_id:
            queryset = queryset.filter(agency_id=agency_id)

        if status_value:
            queryset = queryset.filter(status=status_value)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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


class AdminFlightTicketViewSet(viewsets.ModelViewSet):
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

        ticket = serializer.save()

        _create_reservation_activity_log(
            self.request,
            ticket.reservation,
            ReservationActivityLog.ActionChoices.FLIGHT_TICKET_ADDED,
            "Flight ticket was added.",
            _flight_ticket_log_metadata(ticket),
        )

    def perform_update(self, serializer):
        _ensure_reservation_is_editable_for_request(
            self.request,
            serializer.instance.reservation,
        )

        ticket = serializer.save()

        _create_reservation_activity_log(
            self.request,
            ticket.reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            "Flight ticket was updated.",
            _flight_ticket_log_metadata(
                ticket,
                updated_fields=list(self.request.data.keys()),
            ),
        )

    def perform_destroy(self, instance):
        _ensure_reservation_is_editable_for_request(self.request, instance.reservation)
        reservation = instance.reservation
        metadata = _flight_ticket_log_metadata(instance)
        instance.delete()
        _create_reservation_activity_log(
            self.request,
            reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            "Flight ticket was deleted.",
            metadata,
        )


class AdminOtherServiceViewSet(viewsets.ModelViewSet):
    queryset = OtherService.objects.select_related(
        "reservation",
        "selling_currency",
        "cost_currency",
    ).order_by("-system_date")
    serializer_class = OtherServiceSerializer
    permission_classes = (ReadOnlyOrReservationOperationsRole,)

    def get_queryset(self):
        queryset = super().get_queryset()
        reservation_id = self.request.query_params.get("reservation")
        if reservation_id:
            queryset = queryset.filter(reservation_id=reservation_id)
        return queryset

    def perform_create(self, serializer):
        reservation = serializer.validated_data.get("reservation")
        _ensure_reservation_is_editable_for_request(self.request, reservation)
        service = serializer.save()
        _create_reservation_activity_log(
            self.request,
            service.reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            f"Other service '{service.service_name}' was added.",
            {"service_id": service.id, "service_name": service.service_name},
        )

    def perform_update(self, serializer):
        _ensure_reservation_is_editable_for_request(
            self.request,
            serializer.instance.reservation,
        )
        service = serializer.save()
        _create_reservation_activity_log(
            self.request,
            service.reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            f"Other service '{service.service_name}' was updated.",
            {"service_id": service.id, "service_name": service.service_name},
        )

    def perform_destroy(self, instance):
        _ensure_reservation_is_editable_for_request(self.request, instance.reservation)
        reservation = instance.reservation
        service_name = instance.service_name
        instance.delete()
        _create_reservation_activity_log(
            self.request,
            reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            f"Other service '{service_name}' was deleted.",
            {"service_name": service_name},
        )

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

        booking = serializer.save()

        _create_reservation_activity_log(
            self.request,
            booking.reservation,
            ReservationActivityLog.ActionChoices.EXCURSION_BOOKING_ADDED,
            "Excursion booking was added.",
            _excursion_booking_log_metadata(booking),
        )

    def perform_update(self, serializer):
        _ensure_reservation_is_editable_for_request(
            self.request,
            serializer.instance.reservation,
        )

        booking = serializer.save()

        _create_reservation_activity_log(
            self.request,
            booking.reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            "Excursion booking was updated.",
            _excursion_booking_log_metadata(
                booking,
                updated_fields=list(self.request.data.keys()),
            ),
        )

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

        service = serializer.save()

        _create_reservation_activity_log(
            self.request,
            service.reservation,
            ReservationActivityLog.ActionChoices.TRANSFER_SERVICE_ADDED,
            "Transfer service was added.",
            _transfer_service_log_metadata(service),
        )

    def perform_update(self, serializer):
        _ensure_reservation_is_editable_for_request(
            self.request,
            serializer.instance.reservation,
        )

        service = serializer.save()

        _create_reservation_activity_log(
            self.request,
            service.reservation,
            ReservationActivityLog.ActionChoices.UPDATED,
            "Transfer service was updated.",
            _transfer_service_log_metadata(
                service,
                updated_fields=list(self.request.data.keys()),
            ),
        )

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