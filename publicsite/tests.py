from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from PIL import Image

from .models import HeroSection


class HeroSectionApiTests(APITestCase):
    def _png_bytes(self):
        image = Image.new("RGB", (1, 1), color=(255, 0, 0))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _admin_client(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            email="admin@example.com",
            password="strong-password",
        )
        client = APIClient()
        client.force_authenticate(user=admin_user)
        return client

    def test_client_hero_includes_image_and_logo_fields(self):
        response = self.client.get(reverse("client-hero-section"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("logo", response.data)
        self.assertIsNone(response.data["logo"])
        self.assertIn("image", response.data)
        self.assertIsNone(response.data["image"])

    def test_admin_can_upload_hero_image(self):
        client = self._admin_client()

        image_file = SimpleUploadedFile(
            "hero-banner.jpg",
            self._png_bytes(),
            content_type="image/png",
        )

        response = client.patch(
            reverse("admin-hero-section"),
            {"image": image_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.data)
        self.assertIn("/media/publicsite/hero/", response.data["image"])
        self.assertIn("hero-banner", HeroSection.get_solo().image.name)

    def test_admin_can_upload_and_change_logo(self):
        client = self._admin_client()

        first_logo = SimpleUploadedFile(
            "brand-logo-v1.png",
            self._png_bytes(),
            content_type="image/png",
        )
        first_response = client.patch(
            reverse("admin-hero-section"),
            {"logo": first_logo},
            format="multipart",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertIn("logo", first_response.data)
        self.assertIn("/media/publicsite/logo/", first_response.data["logo"])
        self.assertIn("brand-logo-v1", HeroSection.get_solo().logo.name)

        second_logo = SimpleUploadedFile(
            "brand-logo-v2.png",
            self._png_bytes(),
            content_type="image/png",
        )
        second_response = client.patch(
            reverse("admin-hero-section"),
            {"logo": second_logo},
            format="multipart",
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn("logo", second_response.data)
        self.assertIn("/media/publicsite/logo/", second_response.data["logo"])
        self.assertIn("brand-logo-v2", HeroSection.get_solo().logo.name)