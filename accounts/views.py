from rest_framework import generics, mixins, permissions, viewsets

from .models import CustomUser
from .serializers import (
	AdminCustomUserSerializer,
	ClientCustomUserSerializer,
	RegisterSerializer,
)


class AdminCustomUserViewSet(viewsets.ModelViewSet):
	queryset = CustomUser.objects.all().order_by("id")
	serializer_class = AdminCustomUserSerializer
	permission_classes = (permissions.IsAdminUser,)


class ClientCustomUserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
	serializer_class = ClientCustomUserSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		return CustomUser.objects.filter(id=self.request.user.id)


class RegisterView(generics.CreateAPIView):
	serializer_class = RegisterSerializer
	permission_classes = (permissions.AllowAny,)
