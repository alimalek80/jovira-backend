from rest_framework import serializers

from .models import ExcursionBooking, ExcursionService, FlightTicket, HotelBooking, Reservation, Tourist, TransferService


class TouristSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Tourist
        fields = (
            "id",
            "reservation",
            "first_name",
            "last_name",
            "sex",
            "age_type",
            "passport_number",
            "nationality",
            "birth_date",
            "passport_expiry_date",
        )
        extra_kwargs = {
            "reservation": {"required": False},
        }


class HotelBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelBooking
        fields = (
            "id",
            "reservation",
            "hotel_room",
            "check_in_date",
            "check_out_date",
            "quantity",
            "status",
            "selling_currency",
            "price",
            "agency_price",
            "cost_currency",
            "cost",
            "cross_currency_rate",
            "confirm_booking_number",
            "agent_confirmation_number",
            "hotel_cancellation_number",
            "internal_note",
            "remarks_for_hotel",
            "is_paid",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        hotel_room = attrs.get("hotel_room", getattr(self.instance, "hotel_room", None))
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 1))
        check_in_date = attrs.get("check_in_date", getattr(self.instance, "check_in_date", None))
        check_out_date = attrs.get("check_out_date", getattr(self.instance, "check_out_date", None))
        status = attrs.get("status", getattr(self.instance, "status", HotelBooking.StatusChoices.PENDING))

        if hotel_room and check_in_date and check_out_date:
            if check_in_date >= check_out_date:
                raise serializers.ValidationError(
                    {"check_out_date": "Check-out date must be after check-in date."}
                )

            if check_in_date < hotel_room.date_from or check_out_date > hotel_room.date_to:
                raise serializers.ValidationError(
                    {
                        "hotel_room": (
                            f"Booking dates must fall within the room's availability window "
                            f"({hotel_room.date_from} – {hotel_room.date_to})."
                        )
                    }
                )

            # Only check availability for non-cancelled bookings
            if status != HotelBooking.StatusChoices.CANCELLED:
                from django.db.models import Q, Sum
                overlapping_qs = HotelBooking.objects.filter(
                    hotel_room=hotel_room,
                    check_in_date__lt=check_out_date,
                    check_out_date__gt=check_in_date,
                ).exclude(status=HotelBooking.StatusChoices.CANCELLED)
                if self.instance:
                    overlapping_qs = overlapping_qs.exclude(pk=self.instance.pk)
                booked = overlapping_qs.aggregate(total=Sum("quantity"))["total"] or 0
                available = hotel_room.availability_count - booked
                if quantity > available:
                    raise serializers.ValidationError(
                        {
                            "quantity": (
                                f"Not enough availability. Requested: {quantity}, "
                                f"Available: {available}."
                            )
                        }
                    )

        return attrs


class FlightTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightTicket
        fields = ("id", "reservation", "flight", "tourist", "ticket_number", "pnr_code")
        read_only_fields = ("id",)


class ExcursionBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcursionBooking
        fields = ("id", "reservation", "excursion", "tourists", "tour_date", "pickup_time")
        read_only_fields = ("id",)


class TransferServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferService
        fields = (
            "id",
            "reservation",
            "transfer",
            "tour_package",
            "service_name",
            "service_date",
            "on_arrival",
            "on_departure",
            "from_location_type",
            "from_location_name",
            "to_location_type",
            "to_location_name",
            "price",
            "agency_price",
            "currency",
            "passengers",
            "external_note",
            "driver_note",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        reservation = attrs.get("reservation", getattr(self.instance, "reservation", None))
        tour_package = attrs.get("tour_package", getattr(self.instance, "tour_package", None))
        on_arrival = attrs.get("on_arrival", getattr(self.instance, "on_arrival", False))
        on_departure = attrs.get("on_departure", getattr(self.instance, "on_departure", False))
        passengers = attrs.get("passengers", None)

        if not on_arrival and not on_departure:
            raise serializers.ValidationError(
                {"on_arrival": "At least one of on_arrival or on_departure must be true."}
            )

        if reservation and tour_package and reservation.tour_package_id and reservation.tour_package_id != tour_package.id:
            raise serializers.ValidationError(
                {"tour_package": "Tour package must match the reservation tour package when reservation has one."}
            )

        if reservation and passengers is not None:
            invalid_passengers = [p.id for p in passengers if p.reservation_id != reservation.id]
            if invalid_passengers:
                raise serializers.ValidationError(
                    {
                        "passengers": (
                            "All passengers must belong to the selected reservation. "
                            f"Invalid passenger IDs: {invalid_passengers}"
                        )
                    }
                )

        return attrs

    def _apply_transfer_defaults(self, validated_data):
        """Auto-populate price/currency from the catalog Transfer if not explicitly provided."""
        transfer = validated_data.get("transfer")
        if not transfer or not transfer.currency:
            return

        request = self.context.get("request")
        user = request.user if request else None

        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            catalog_price = transfer.agency_price
        else:
            catalog_price = transfer.public_price

        if catalog_price is not None and "price" not in self.initial_data:
            validated_data.setdefault("price", catalog_price)
        if transfer.agency_price is not None and "agency_price" not in self.initial_data:
            validated_data.setdefault("agency_price", transfer.agency_price)
        if "currency" not in self.initial_data:
            validated_data.setdefault("currency", transfer.currency)

    def create(self, validated_data):
        self._apply_transfer_defaults(validated_data)
        return super().create(validated_data)


class ReservationSerializer(serializers.ModelSerializer):
    tourists = TouristSerializer(many=True, required=False)
    hotel_bookings = HotelBookingSerializer(many=True, read_only=True)
    flight_tickets = FlightTicketSerializer(many=True, read_only=True)
    transfer_services = TransferServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "id",
            "reservation_number",
            "created_at",
            "currency",
            "status",
            "agency",
            "tour_package",
            "tourists",
            "hotel_bookings",
            "flight_tickets",
            "transfer_services",
        )
        read_only_fields = ("id", "created_at")
        extra_kwargs = {
            "agency": {"required": False, "allow_null": True},
            "tour_package": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        # Admin endpoints can explicitly set any agency value.
        if not user or not user.is_authenticated or user.is_staff or user.is_superuser:
            return attrs

        provided_agency = attrs.get("agency", getattr(self.instance, "agency", None))

        if getattr(user, "role", None) == "AGENCY":
            if not getattr(user, "agency", None):
                raise serializers.ValidationError(
                    {"agency": "Your account has agency role but no agency is assigned."}
                )
            if provided_agency and provided_agency.id != user.agency_id:
                raise serializers.ValidationError(
                    {"agency": "Agency users can only create reservations for their own agency."}
                )
            attrs["agency"] = user.agency
        else:
            # NORMAL users create direct reservations without agency.
            attrs["agency"] = None

        return attrs

    def create(self, validated_data):
        tourists_data = validated_data.pop("tourists", [])
        reservation = Reservation.objects.create(**validated_data)

        for tourist_data in tourists_data:
            tourist_data.pop("reservation", None)
            Tourist.objects.create(reservation=reservation, **tourist_data)

        return reservation

    def update(self, instance, validated_data):
        tourists_data = validated_data.pop("tourists", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tourists_data is not None:
            existing_tourists = {tourist.id: tourist for tourist in instance.tourists.all()}

            for tourist_data in tourists_data:
                tourist_id = tourist_data.get("id")
                tourist_data.pop("reservation", None)

                if tourist_id:
                    tourist_obj = existing_tourists.get(tourist_id)
                    if tourist_obj is None:
                        raise serializers.ValidationError(
                            {"tourists": f"Tourist with id {tourist_id} does not belong to this reservation."}
                        )

                    for attr, value in tourist_data.items():
                        setattr(tourist_obj, attr, value)
                    tourist_obj.save()
                else:
                    Tourist.objects.create(reservation=instance, **tourist_data)

        return instance


class ExcursionServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcursionService
        fields = (
            "id",
            "system_date",
            "excursion_date",
            "excursion",
            "is_combo",
            "pickup_point",
            "price",
            "selling_currency",
            "cost",
            "cost_currency",
            "cross_currency_rate",
            "is_paid",
            "confirm_booking_number",
            "agent_confirmation_number",
            "note",
        )
        read_only_fields = ("id", "system_date")

    def _apply_excursion_defaults(self, validated_data):
        """
        If price/cost/selling_currency/cost_currency are not explicitly provided,
        auto-populate them from the linked excursion's catalog price and currency.
        """
        excursion = validated_data.get("excursion")
        if not excursion or not excursion.currency:
            return

        request = self.context.get("request")
        user = request.user if request else None

        # Choose catalog price based on user role (agency → agency_price, else public_price)
        if user and user.is_authenticated and getattr(user, "can_access_agency_prices", False):
            catalog_price = excursion.agency_price
        else:
            catalog_price = excursion.public_price

        if catalog_price is not None and "price" not in self.initial_data:
            validated_data.setdefault("price", catalog_price)
        if excursion.currency is not None and "selling_currency" not in self.initial_data:
            validated_data.setdefault("selling_currency", excursion.currency)
        if catalog_price is not None and "cost" not in self.initial_data:
            validated_data.setdefault("cost", catalog_price)
        if excursion.currency is not None and "cost_currency" not in self.initial_data:
            validated_data.setdefault("cost_currency", excursion.currency)

    def create(self, validated_data):
        self._apply_excursion_defaults(validated_data)
        return super().create(validated_data)
