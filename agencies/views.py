from rest_framework import generics, permissions, response, status, viewsets
from rest_framework.decorators import action

from accounts.models import CustomUser

from .models import Agency
from .serializers import AdminAgencySerializer, AgencyRegisterSerializer, ClientAgencySerializer


class AdminAgencyViewSet(viewsets.ModelViewSet):
	queryset = Agency.objects.all().order_by("name")
	serializer_class = AdminAgencySerializer
	permission_classes = (permissions.IsAdminUser,)

	@action(detail=True, methods=["post"])
	def approve(self, request, pk=None):
		agency = self.get_object()
		agency.approve()
		CustomUser.objects.filter(agency=agency, role=CustomUser.RoleChoices.AGENCY).update(is_active=True)
		return response.Response(self.get_serializer(agency).data, status=status.HTTP_200_OK)


class ClientAgencyViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Agency.objects.filter(is_approved=True).order_by("name")
	serializer_class = ClientAgencySerializer
	permission_classes = (permissions.AllowAny,)


class AgencyRegisterView(generics.CreateAPIView):
	serializer_class = AgencyRegisterSerializer
	permission_classes = (permissions.AllowAny,)
