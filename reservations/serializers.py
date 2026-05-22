from rest_framework import serializers

from .models import ExcursionBooking, FlightTicket, HotelBooking, Reservation, Tourist, TransferService


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
            "hotel",
            "check_in_date",
            "check_out_date",
            "board_type",
            "is_paid",
        )
        read_only_fields = ("id",)


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
