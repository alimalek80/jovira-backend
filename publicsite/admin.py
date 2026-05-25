from django.contrib import admin

from .models import HeroSection


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "badge_text", "headline", "logo", "image", "updated_at")

    def has_add_permission(self, request):
        return not HeroSection.objects.exists()
