from rest_framework import serializers

from .models import Excursion, Flight, Hotel, TourPackage


class HotelSerializer(serializers.ModelSerializer):
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
        )
        read_only_fields = ("id",)


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
        )
        read_only_fields = ("id",)
