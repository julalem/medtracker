from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from medtrackerapp.models import Medication

class ExpectedDosesAPITests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="TestMed",
            dosage_mg=50,
            prescribed_per_day=2
        )

    def test_missing_days_parameter_returns_400(self):
        url = reverse("medication-expected-doses", args=[self.med.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_days_not_integer_returns_400(self):
        url = reverse("medication-expected-doses", args=[self.med.id]) + "?days=abc"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_days_zero_or_negative_returns_400(self):
        url = reverse("medication-expected-doses", args=[self.med.id]) + "?days=0"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        url = reverse("medication-expected-doses", args=[self.med.id]) + "?days=-5"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_medication_with_zero_prescribed_per_day_raises_valueerror_from_model_returns_400(self):
        med2 = Medication.objects.create(name="ZeroMed", dosage_mg=10, prescribed_per_day=0)
        url = reverse("medication-expected-doses", args=[med2.id]) + "?days=1"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_success_returns_expected_payload_and_200(self):
        url = reverse("medication-expected-doses", args=[self.med.id]) + "?days=3"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json = resp.json()
        self.assertIn("medication_id", json)
        self.assertIn("days", json)
        self.assertIn("expected_doses", json)
        self.assertEqual(json["medication_id"], self.med.id)
        self.assertEqual(json["days"], 3)
        self.assertEqual(json["expected_doses"], self.med.expected_doses(3))
