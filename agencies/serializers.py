from rest_framework import serializers
from django.db import transaction

from accounts.models import CustomUser
from .models import Agency


class AdminAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = (
            "id",
            "name",
            "agency_type",
            "contact_person",
            "email",
            "phone",
            "mobile_phone",
            "skype_id",
            "icq",
            "is_approved",
            "approved_at",
        )
        read_only_fields = ("id",)


class ClientAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = (
            "id",
            "name",
            "agency_type",
            "contact_person",
            "email",
            "phone",
            "mobile_phone",
            "skype_id",
            "icq",
        )
        read_only_fields = ("id",)


class AgencyRegisterSerializer(serializers.ModelSerializer):
    account_email = serializers.EmailField(write_only=True)
    account_first_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    account_last_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    account_phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Agency
        fields = (
            "id",
            "name",
            "agency_type",
            "contact_person",
            "email",
            "phone",
            "mobile_phone",
            "skype_id",
            "icq",
            "is_approved",
            "approved_at",
            "account_email",
            "account_first_name",
            "account_last_name",
            "account_phone_number",
            "password",
            "password2",
        )
        read_only_fields = ("id", "is_approved", "approved_at")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if CustomUser.objects.filter(email=attrs["account_email"]).exists():
            raise serializers.ValidationError({"account_email": "This email is already registered."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2")
        account_email = validated_data.pop("account_email")
        account_first_name = validated_data.pop("account_first_name", "")
        account_last_name = validated_data.pop("account_last_name", "")
        account_phone_number = validated_data.pop("account_phone_number", None)

        with transaction.atomic():
            agency_email = validated_data.get("email") or account_email
            agency = Agency.objects.create(**{**validated_data, "email": agency_email})
            CustomUser.objects.create_user(
                email=account_email,
                password=password,
                first_name=account_first_name,
                last_name=account_last_name,
                phone_number=account_phone_number,
                role=CustomUser.RoleChoices.AGENCY,
                agency=agency,
                is_active=False,
                is_staff=False,
                is_superuser=False,
            )

        return agency
