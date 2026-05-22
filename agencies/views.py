from rest_framework import permissions, viewsets

from .models import Agency
from .serializers import AgencySerializer


class AdminAgencyViewSet(viewsets.ModelViewSet):
	queryset = Agency.objects.all().order_by("name")
	serializer_class = AgencySerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientAgencyViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Agency.objects.all().order_by("name")
	serializer_class = AgencySerializer
	permission_classes = (permissions.AllowAny,)
