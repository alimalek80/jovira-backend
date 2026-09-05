from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminAgencyViewSet, AdminSupplierViewSet, AgencyRegisterView, ClientAgencyViewSet

admin_router = DefaultRouter()
admin_router.register(r"agencies", AdminAgencyViewSet, basename="admin-agencies")
admin_router.register(r"suppliers", AdminSupplierViewSet, basename="admin-suppliers")

client_router = DefaultRouter()
client_router.register(r"agencies", ClientAgencyViewSet, basename="client-agencies")

urlpatterns = [
    path("admin/", include(admin_router.urls)),
    path("client/", include(client_router.urls)),
    path("client/register/", AgencyRegisterView.as_view(), name="agency-register"),
]
