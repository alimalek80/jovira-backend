from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Agency


class AgencyOnboardingTests(APITestCase):
	def test_register_creates_pending_agency_and_inactive_agency_user(self):
		payload = {
			"name": "Skyline Travels",
			"agency_type": "B2B",
			"contact_person": "Aylin Kaya",
			"email": "contact@skyline.example",
			"account_email": "owner@skyline.example",
			"password": "VeryStrongPass1",
			"password2": "VeryStrongPass1",
		}

		response = self.client.post(reverse("agency-register"), payload, format="json")

		self.assertEqual(response.status_code, 201)
		agency = Agency.objects.get(name="Skyline Travels")
		self.assertFalse(agency.is_approved)
		self.assertIsNone(agency.approved_at)

		user = get_user_model().objects.get(email="owner@skyline.example")
		self.assertEqual(user.role, get_user_model().RoleChoices.AGENCY)
		self.assertEqual(user.agency_id, agency.id)
		self.assertFalse(user.is_active)

		login_response = self.client.post(
			reverse("token_obtain_pair"),
			{"email": "owner@skyline.example", "password": "VeryStrongPass1"},
			format="json",
		)
		self.assertEqual(login_response.status_code, 401)

	def test_client_agency_list_shows_only_approved(self):
		approved = Agency.objects.create(
			name="Approved Agency",
			agency_type="B2B",
			contact_person="Approved Person",
			is_approved=True,
		)
		Agency.objects.create(
			name="Pending Agency",
			agency_type="B2B",
			contact_person="Pending Person",
			is_approved=False,
		)

		response = self.client.get(reverse("client-agencies-list"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["id"], approved.id)

	def test_admin_approval_activates_agency_user_and_exposes_agency(self):
		user_model = get_user_model()
		admin_user = user_model.objects.create_superuser(
			email="admin-approval@example.com",
			password="StrongAdminPass1",
		)

		pending_agency = Agency.objects.create(
			name="Pending For Approval",
			agency_type="B2B",
			contact_person="Person",
			is_approved=False,
		)
		agency_user = user_model.objects.create_user(
			email="pending@agency.example",
			password="AgencyPass123",
			role=user_model.RoleChoices.AGENCY,
			agency=pending_agency,
			is_active=False,
		)

		self.client.force_authenticate(user=admin_user)
		approve_response = self.client.post(reverse("admin-agencies-approve", args=[pending_agency.id]))

		self.assertEqual(approve_response.status_code, 200)

		pending_agency.refresh_from_db()
		agency_user.refresh_from_db()
		self.assertTrue(pending_agency.is_approved)
		self.assertIsNotNone(pending_agency.approved_at)
		self.assertTrue(agency_user.is_active)

		self.client.force_authenticate(user=None)
		login_response = self.client.post(
			reverse("token_obtain_pair"),
			{"email": "pending@agency.example", "password": "AgencyPass123"},
			format="json",
		)
		self.assertEqual(login_response.status_code, 200)
		self.assertIn("access", login_response.data)

		client_list_response = self.client.get(reverse("client-agencies-list"))
		self.assertEqual(client_list_response.status_code, 200)
		returned_ids = [item["id"] for item in client_list_response.data]
		self.assertIn(pending_agency.id, returned_ids)
