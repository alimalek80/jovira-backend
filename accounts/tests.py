from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser


class DepartmentFieldSecurityTests(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            email="admin@example.com",
            role=CustomUser.RoleChoices.ADMIN,
        )
        self.sales_user = CustomUser.objects.create_user(
            email="sales@example.com",
            role=CustomUser.RoleChoices.SALES,
            department=CustomUser.DepartmentChoices.SALES,
        )

    def test_admin_can_set_department(self):
        self.sales_user.department = None
        self.sales_user.save(update_fields=["department"])
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            reverse("admin-users-detail", kwargs={"pk": self.sales_user.pk}),
            {"department": "SALES"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["department"], "SALES")
        self.sales_user.refresh_from_db()
        self.assertEqual(self.sales_user.department, "SALES")

    def test_non_admin_cannot_change_own_department(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.patch(
            reverse("client-users-detail", kwargs={"pk": self.sales_user.pk}),
            {"department": "MANAGEMENT"},
            format="json",
        )

        self.sales_user.refresh_from_db()
        self.assertEqual(self.sales_user.department, "SALES")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["department"], "SALES")

    def test_non_admin_cannot_reach_admin_user_endpoint(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.patch(
            reverse("admin-users-detail", kwargs={"pk": self.sales_user.pk}),
            {"department": "MANAGEMENT"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_department_defaults_to_null(self):
        user = CustomUser.objects.create_user(email="default@example.com")

        self.assertIsNone(user.department)

    def test_invalid_department_value_is_rejected(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            reverse("admin-users-detail", kwargs={"pk": self.sales_user.pk}),
            {"department": "MARKETING"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
