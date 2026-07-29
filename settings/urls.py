from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmailConfigViewSet, ReservationEmailViewSet, ReservationEmailHistoryViewSet

router = DefaultRouter()
router.register(r'email-config', EmailConfigViewSet, basename='email-config')
router.register(r'reservation-email', ReservationEmailViewSet, basename='reservation-email')
router.register(r'reservation-email-history', ReservationEmailHistoryViewSet, basename='reservation-email-history')

urlpatterns = [
    path('', include(router.urls)),
]