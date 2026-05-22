from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminCustomUserViewSet, ClientCustomUserViewSet

admin_router = DefaultRouter()
admin_router.register(r"users", AdminCustomUserViewSet, basename="admin-users")

client_router = DefaultRouter()
client_router.register(r"users", ClientCustomUserViewSet, basename="client-users")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("client/", include(client_router.urls)),
]
