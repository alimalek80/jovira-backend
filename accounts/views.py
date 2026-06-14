from rest_framework import generics, mixins, permissions, viewsets
from .models import CustomUser
from .permissions import IsAdminRole
from .serializers import (
    AdminCustomUserSerializer,
    ClientCustomUserSerializer,
    RegisterSerializer,
)

class AdminCustomUserViewSet(viewsets.ModelViewSet):
    """
    User Management: Restricted strictly to ADMIN role and Superusers.
    Prevents other staff (Sales, Finance, etc.) from modifying users or roles.
    """
    queryset = CustomUser.objects.all().order_by("-id") # Order by newest first
    serializer_class = AdminCustomUserSerializer
    permission_classes = (IsAdminRole,) 
    
    # All creation/update operations are secure since the serializer enforces the role field.


class ClientCustomUserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Profile Self-Service: All authenticated users can view/update their own profile.
    The serializer limits fields like 'role' to read-only for security.
    """
    serializer_class = ClientCustomUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Users can only see their own profile
        return CustomUser.objects.filter(id=self.request.user.id)


class RegisterView(generics.CreateAPIView):
    """
    Public Registration: Open for anyone to create a NORMAL user account.
    """
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)