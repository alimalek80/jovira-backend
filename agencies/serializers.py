from rest_framework import serializers

from .models import Agency


class AgencySerializer(serializers.ModelSerializer):
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
