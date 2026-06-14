from django.db import transaction

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import CustomUser
from accounts.permissions import IsAdminRole

from .models import Agency
from .serializers import (
    AdminAgencySerializer,
    AgencyRegisterSerializer,
    ClientAgencySerializer,
)


class AdminAgencyViewSet(viewsets.ModelViewSet):
    queryset = Agency.objects.all().order_by("name")
    serializer_class = AdminAgencySerializer
    permission_classes = (IsAdminRole,)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        agency = self.get_object()

        with transaction.atomic():
            agency.approve()
            CustomUser.objects.filter(
                agency=agency,
                role=CustomUser.RoleChoices.AGENCY,
            ).update(is_active=True)

        return Response(
            self.get_serializer(agency).data,
            status=status.HTTP_200_OK,
        )


class ClientAgencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Agency.objects.filter(is_approved=True).order_by("name")
    serializer_class = ClientAgencySerializer
    permission_classes = (permissions.AllowAny,)


class AgencyRegisterView(generics.CreateAPIView):
    serializer_class = AgencyRegisterSerializer
    permission_classes = (permissions.AllowAny,)