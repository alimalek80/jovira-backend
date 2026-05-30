from rest_framework import serializers

from .models import Excursion, Flight, Hotel, TourPackage, HotelFeature, HotelImage, Transfer, TransferProvider



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


class HotelSerializer(serializers.ModelSerializer):
    features = HotelFeatureSerializer(many=True, read_only=True)
    gallery_images = HotelImageSerializer(many=True, read_only=True)

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
            "currency",
            "price",
            "agency_price",
            "cost_price",
            "description",
            "description_en",
            "description_tr",
            "description_ru",
            "main_image",
            "features",
            "gallery_images",
        )
        read_only_fields = ("id",)


class ClientHotelSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    features = HotelFeatureSerializer(many=True, read_only=True)
    gallery_images = HotelImageSerializer(many=True, read_only=True)

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
            "currency",
            "price",
            "description",
            "description_en",
            "description_tr",
            "description_ru",
            "main_image",
            "features",
            "gallery_images",
        )
        read_only_fields = ("id",)

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return obj.get_price_for_user(user)


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


class TourPackageSerializer(serializers.ModelSerializer):
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
            "currency",
            "public_price",
            "agency_price",
            "cost_price",
        )
        read_only_fields = ("id",)


class ClientTourPackageSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

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
            "currency",
            "price",
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
