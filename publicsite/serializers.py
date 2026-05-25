from rest_framework import serializers

from .models import HeroSection


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = (
            "id",
            "badge_text",
            "logo",
            "image",
            "headline",
            "description",
            "search_placeholder",
            "search_button_text",
            "updated_at",
        )
        read_only_fields = ("id", "updated_at")
