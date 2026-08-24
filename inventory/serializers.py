from rest_framework import serializers
from decimal import Decimal
from finance.utils import convert_amount

from .models import Excursion, Flight, Hotel, HotelRoom, TourPackage, TourPackageGalleryImage, HotelFeature, HotelImage, Transfer, TransferProvider



class HotelFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelFeature
        fields = ("id", "name", "name_en", "name_tr", "name_ru")
        read_only_fields = ("id",)


class HotelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelImage
        fields = ("id", "hotel", "image", "alt_text", "order")
        read_only_fields = ("id",)


class HotelRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelRoom
        fields = (
            "id",
            "hotel",
            "room_type",
            "board_type",
            "date_from",
            "date_to",
            "availability_count",
            "currency",
            "public_price",
            "agency_price",
            "cost_price",
            "note",
        )
        read_only_fields = ("id",)


class ClientHotelRoomSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = HotelRoom
        fields = (
            "id",
            "hotel",
            "room_type",
            "board_type",
            "date_from",
            "date_to",
            "availability_count",
            "currency",
            "price",
            "note",
        )
        read_only_fields = ("id",)

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return obj.get_price_for_user(user)


class HotelSerializer(serializers.ModelSerializer):
    features = HotelFeatureSerializer(many=True, read_only=True)
    gallery_images = HotelImageSerializer(many=True, read_only=True)
    rooms = HotelRoomSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = (
            "id",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "city",
            "city_en",
            "city_tr",
            "city_ru",
            "stars",
            "description",
            "description_en",
            "description_tr",
            "description_ru",
            "main_image",
            "features",
            "gallery_images",
            "rooms",
        )
        read_only_fields = ("id",)


class ClientHotelSerializer(serializers.ModelSerializer):
    features = HotelFeatureSerializer(many=True, read_only=True)
    gallery_images = HotelImageSerializer(many=True, read_only=True)
    rooms = ClientHotelRoomSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = (
            "id",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "city",
            "city_en",
            "city_tr",
            "city_ru",
            "stars",
            "description",
            "description_en",
            "description_tr",
            "description_ru",
            "main_image",
            "features",
            "gallery_images",
            "rooms",
        )
        read_only_fields = ("id",)


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "flight_number",
            "airline",
            "origin",
            "origin_en",
            "origin_tr",
            "origin_ru",
            "destination",
            "destination_en",
            "destination_tr",
            "destination_ru",
            "departure_time",
            "arrival_time",
            "currency",
            "price",
            "agency_price",
            "cost_price",
        )
        read_only_fields = ("id",)


class ClientFlightSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = (
            "id",
            "flight_number",
            "airline",
            "origin",
            "origin_en",
            "origin_tr",
            "origin_ru",
            "destination",
            "destination_en",
            "destination_tr",
            "destination_ru",
            "departure_time",
            "arrival_time",
            "currency",
            "price",
        )
        read_only_fields = ("id",)

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return obj.get_price_for_user(user)


class TourPackageGalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourPackageGalleryImage
        fields = ("id", "tour_package", "image", "alt_text", "order")
        read_only_fields = ("id",)


class TourPackageSerializer(serializers.ModelSerializer):
    minimum_cost_floor = serializers.SerializerMethodField(read_only=True)
    gallery_images = TourPackageGalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = TourPackage
        fields = (
            "id",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "destination",
            "destination_en",
            "destination_tr",
            "destination_ru",
            "days",
            "nights",
            "main_image",
            "currency",
            "public_price",
            "agency_price",
            "cost_price",
            "flights",
            "hotels",
            "transfers",
            "excursions",
            "minimum_cost_floor",
            "gallery_images",
        )
        read_only_fields = ("id",)

    def get_minimum_cost_floor(self, obj):
        return obj.calculate_minimum_cost_floor()

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = self.instance
        currency = attrs.get("currency", getattr(instance, "currency", None))
        nights = attrs.get("nights", getattr(instance, "nights", 1))

        flights = attrs.get("flights", instance.flights.all() if instance else [])
        transfers = attrs.get("transfers", instance.transfers.all() if instance else [])
        excursions = attrs.get("excursions", instance.excursions.all() if instance else [])

        minimum_floor = Decimal("0.00")
        for item in flights:
            minimum_floor += convert_amount(item.cost_price or Decimal("0.00"), item.currency_id, getattr(currency, "id", None))

        for item in transfers:
            minimum_floor += convert_amount(item.cost_price or Decimal("0.00"), item.currency_id, getattr(currency, "id", None))

        for item in excursions:
            minimum_floor += convert_amount(item.cost_price or Decimal("0.00"), item.currency_id, getattr(currency, "id", None))

        minimum_floor = minimum_floor.quantize(Decimal("0.01"))

        cost_price = attrs.get("cost_price", getattr(instance, "cost_price", None))
        agency_price = attrs.get("agency_price", getattr(instance, "agency_price", None))
        public_price = attrs.get("public_price", getattr(instance, "public_price", None))

        if cost_price is not None and cost_price < minimum_floor:
            raise serializers.ValidationError({
                "cost_price": "Cost price cannot be lower than minimum component cost floor."
            })

        if agency_price is not None and agency_price < minimum_floor:
            raise serializers.ValidationError({
                "agency_price": "Agency price cannot be lower than minimum component cost floor."
            })

        if public_price is not None and public_price < minimum_floor:
            raise serializers.ValidationError({
                "public_price": "Public price cannot be lower than minimum component cost floor."
            })

        if public_price is not None and agency_price is not None and public_price < agency_price:
            raise serializers.ValidationError({
                "public_price": "Public price cannot be lower than agency price."
            })

        return attrs


class ClientTourPackageSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    gallery_images = TourPackageGalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = TourPackage
        fields = (
            "id",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "destination",
            "destination_en",
            "destination_tr",
            "destination_ru",
            "days",
            "nights",
            "main_image",
            "currency",
            "price",
            "gallery_images",
        )
        read_only_fields = ("id",)

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return obj.get_price_for_user(user)


class ExcursionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Excursion
        fields = (
            "id",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "city",
            "city_en",
            "city_tr",
            "city_ru",
            "duration_hours",
            "currency",
            "public_price",
            "agency_price",
            "cost_price",
        )
        read_only_fields = ("id",)


class ClientExcursionSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Excursion
        fields = (
            "id",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "city",
            "city_en",
            "city_tr",
            "city_ru",
            "duration_hours",
            "currency",
            "price",
        )
        read_only_fields = ("id",)

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return obj.get_price_for_user(user)


class TransferProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferProvider
        fields = ("id", "name", "provider_type", "contact_person", "phone", "email", "notes")
        read_only_fields = ("id",)


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = (
            "id",
            "provider",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "from_location",
            "from_location_en",
            "from_location_tr",
            "from_location_ru",
            "to_location",
            "to_location_en",
            "to_location_tr",
            "to_location_ru",
            "vehicle_type",
            "vehicle_type_en",
            "vehicle_type_tr",
            "vehicle_type_ru",
            "capacity",
            "currency",
            "public_price",
            "agency_price",
            "cost_price",
        )
        read_only_fields = ("id",)


class ClientTransferSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
        fields = (
            "id",
            "provider",
            "name",
            "name_en",
            "name_tr",
            "name_ru",
            "from_location",
            "from_location_en",
            "from_location_tr",
            "from_location_ru",
            "to_location",
            "to_location_en",
            "to_location_tr",
            "to_location_ru",
            "vehicle_type",
            "vehicle_type_en",
            "vehicle_type_tr",
            "vehicle_type_ru",
            "capacity",
            "currency",
            "price",
        )
        read_only_fields = ("id",)

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return obj.get_price_for_user(user)
