from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmailConfigViewSet

router = DefaultRouter()
router.register(r'email-config', EmailConfigViewSet, basename='email-config')

urlpatterns = [
    path('', include(router.urls)),
]