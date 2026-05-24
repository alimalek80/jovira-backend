from django.urls import path

from .views import AdminHeroSectionView, ClientHeroSectionView

urlpatterns = [
    path("client/hero/", ClientHeroSectionView.as_view(), name="client-hero-section"),
    path("admin/hero/", AdminHeroSectionView.as_view(), name="admin-hero-section"),
]
