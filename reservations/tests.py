from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser
from agencies.models import Agency
from finance.models import Currency
from inventory.models import Flight, Hotel, TourPackage

from .models import FlightTicket, Reservation, Tourist
from .serializers import (
	FlightTicketSerializer,
	HotelBookingSerializer,
	ReservationSerializer,
	TransferServiceSerializer,
)


class TransferServiceSerializerTests(TestCase):
	def setUp(self):
		self.currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
		self.hotel = Hotel.objects.create(name="City Hotel", city="Istanbul", stars=4)
		self.flight = Flight.objects.create(
			flight_number="JV100",
			airline="Jovira Air",
			origin="Istanbul",
			destination="Antalya",
			departure_time=timezone.now(),
			arrival_time=timezone.now() + timezone.timedelta(hours=1),
		)
		self.agency = Agency.objects.create(
			name="Demo Agency",
			agency_type="B2B",
			contact_person="John Manager",
		)
		self.tour_package = TourPackage.objects.create(
			name="Antalya Package",
			destination="Antalya",
			days=5,
			nights=4,
		)
		self.reservation = Reservation.objects.create(
			reservation_number="RSV-1001",
			currency=self.currency,
			agency=self.agency,
			tour_package=self.tour_package,
		)
		self.other_reservation = Reservation.objects.create(
			reservation_number="RSV-1002",
			currency=self.currency,
			agency=self.agency,
		)
		self.tourist = Tourist.objects.create(
			reservation=self.reservation,
			first_name="Alice",
			last_name="Brown",
			sex=Tourist.SexChoices.FEMALE,
			age_type=Tourist.AgeTypeChoices.ADULT,
		)
		self.other_tourist = Tourist.objects.create(
			reservation=self.other_reservation,
			first_name="Bob",
			last_name="Green",
			sex=Tourist.SexChoices.MALE,
			age_type=Tourist.AgeTypeChoices.ADULT,
		)

	def _base_payload(self):
		return {
			"reservation": self.reservation.id,
			"tour_package": self.tour_package.id,
			"service_name": "Private Airport Transfer",
			"service_date": "2026-06-01",
			"on_arrival": True,
			"on_departure": False,
			"from_location_type": "AIRPORT",
			"from_location_name": "AYT Airport",
			"to_location_type": "HOTEL",
			"to_location_name": "Blue Sea Hotel",
			"price": "45.00",
			"currency": self.currency.id,
			"passengers": [self.tourist.id],
			"external_note": "Guest asked for child seat",
			"driver_note": "Meet at Gate 3",
		}

	def test_rejects_when_both_arrival_and_departure_are_false(self):
		payload = self._base_payload()
		payload["on_arrival"] = False
		payload["on_departure"] = False

		serializer = TransferServiceSerializer(data=payload)

		self.assertFalse(serializer.is_valid())
		self.assertIn("on_arrival", serializer.errors)

	def test_rejects_passenger_not_in_same_reservation(self):
		payload = self._base_payload()
		payload["passengers"] = [self.other_tourist.id]

		serializer = TransferServiceSerializer(data=payload)

		self.assertFalse(serializer.is_valid())
		self.assertIn("passengers", serializer.errors)

	def test_accepts_reservation_without_tour_package(self):
		payload = {
			"reservation_number": "RSV-1003",
			"currency": self.currency.id,
			"status": Reservation.StatusChoices.DRAFT,
			"agency": self.agency.id,
			"tour_package": None,
		}

		serializer = ReservationSerializer(data=payload)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		reservation = serializer.save()
		self.assertIsNone(reservation.tour_package)

	def test_accepts_hotel_booking_for_reservation_without_tour_package(self):
		reservation = Reservation.objects.create(
			reservation_number="RSV-1004",
			currency=self.currency,
			agency=self.agency,
			tour_package=None,
		)
		payload = {
			"reservation": reservation.id,
			"hotel": self.hotel.id,
			"check_in_date": "2026-06-05",
			"check_out_date": "2026-06-08",
			"board_type": "BB",
			"is_paid": False,
		}

		serializer = HotelBookingSerializer(data=payload)

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_accepts_flight_ticket_for_reservation_without_tour_package(self):
		reservation = Reservation.objects.create(
			reservation_number="RSV-1005",
			currency=self.currency,
			agency=self.agency,
			tour_package=None,
		)
		tourist = Tourist.objects.create(
			reservation=reservation,
			first_name="Mona",
			last_name="Turan",
			sex=Tourist.SexChoices.FEMALE,
			age_type=Tourist.AgeTypeChoices.ADULT,
		)
		payload = {
			"reservation": reservation.id,
			"flight": self.flight.id,
			"tourist": tourist.id,
			"ticket_number": "TK-9988",
			"pnr_code": "PNR55",
		}

		serializer = FlightTicketSerializer(data=payload)

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_accepts_transfer_without_tour_package(self):
		payload = self._base_payload()
		payload["tour_package"] = None

		serializer = TransferServiceSerializer(data=payload)

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_flight_ticket_serializer_expands_flight_and_tourist_in_output(self):
		reservation = Reservation.objects.create(
			reservation_number="RSV-1006",
			currency=self.currency,
			agency=self.agency,
		)
		tourist = Tourist.objects.create(
			reservation=reservation,
			first_name="Lina",
			last_name="Kaya",
			sex=Tourist.SexChoices.FEMALE,
			age_type=Tourist.AgeTypeChoices.ADULT,
		)
		ticket = FlightTicket.objects.create(
			reservation=reservation,
			flight=self.flight,
			tourist=tourist,
			ticket_number="TK-5544",
			pnr_code="ABCD12",
		)

		data = FlightTicketSerializer(instance=ticket).data

		self.assertEqual(data["flight"]["id"], self.flight.id)
		self.assertEqual(data["flight"]["flight_number"], self.flight.flight_number)
		self.assertEqual(data["flight"]["airline"], self.flight.airline)
		self.assertEqual(data["tourist"]["id"], tourist.id)
		self.assertEqual(data["tourist"]["first_name"], tourist.first_name)
		self.assertEqual(data["tourist"]["last_name"], tourist.last_name)


class FlightTicketAdminApiTests(APITestCase):
	def setUp(self):
		self.currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
		self.agency = Agency.objects.create(
			name="Demo Agency",
			agency_type="B2B",
			contact_person="John Manager",
		)
		self.flight = Flight.objects.create(
			flight_number="JV200",
			airline="Jovira Air",
			origin="Istanbul",
			destination="Antalya",
			departure_time=timezone.now(),
			arrival_time=timezone.now() + timezone.timedelta(hours=1),
		)
		self.reservation = Reservation.objects.create(
			reservation_number="RSV-2001",
			currency=self.currency,
			agency=self.agency,
		)
		self.tourist = Tourist.objects.create(
			reservation=self.reservation,
			first_name="Sara",
			last_name="Demir",
			sex=Tourist.SexChoices.FEMALE,
			age_type=Tourist.AgeTypeChoices.ADULT,
		)
		self.ticket = FlightTicket.objects.create(
			reservation=self.reservation,
			flight=self.flight,
			tourist=self.tourist,
			ticket_number="TK-2001",
			pnr_code="ZXCV12",
		)
		self.user = CustomUser.objects.create_user(
			email="reservation@example.com",
			password="pass1234",
			username="reservation.user",
			role=CustomUser.RoleChoices.RESERVATION,
		)
		self.client.force_authenticate(user=self.user)

	def test_admin_flight_ticket_delete_is_allowed(self):
		response = self.client.delete(reverse("admin-flight-tickets-detail", args=[self.ticket.id]))

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(FlightTicket.objects.filter(id=self.ticket.id).exists())
