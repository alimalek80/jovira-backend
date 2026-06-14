from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from accounts.permissions import IsAdminRole

from .models import HeroSection
from .serializers import HeroSectionSerializer


class ClientHeroSectionView(generics.RetrieveAPIView):
    serializer_class = HeroSectionSerializer
    permission_classes = (permissions.AllowAny,)

    def get_object(self):
        return HeroSection.get_solo()


class AdminHeroSectionView(generics.RetrieveUpdateAPIView):
    serializer_class = HeroSectionSerializer
    permission_classes = (IsAdminRole,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def get_object(self):
        return HeroSection.get_solo()