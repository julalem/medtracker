from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta


class MedicationViewTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    # List
    def test_list_medications(self):
        url = reverse("medication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")
        self.assertEqual(response.data[0]["dosage_mg"], 100)
        self.assertEqual(response.data[0]["prescribed_per_day"], 2)

    # Create
    def test_create_medication(self):
        url = reverse("medication-list")
        payload = {
            "name": "Ibuprofen",
            "dosage_mg": 200,
            "prescribed_per_day": 1
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_medication_invalid(self):
        url = reverse("medication-list")
        payload = {
            "name": "",
            "dosage_mg": -10,
            "prescribed_per_day": 0
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Retrieve
    def test_retrieve_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Update
    def test_update_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        payload = {"name": "Updated", "dosage_mg": 150, "prescribed_per_day": 1}
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated")

    # Delete
    def test_delete_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Get external info (mocked)
    @patch("medtrackerapp.services.requests.get")
    def test_external_info_mocked(self, mock_get):
        url = reverse("medication-get-external-info", args=[self.med.id])

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [{
                "openfda": {"generic_name": ["Aspirin"], "manufacturer_name": ["Bayer"]},
                "warnings": ["Warning text"],
                "purpose": ["Pain relief"]
            }]
        }

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data)
        self.assertEqual(response.data["name"], "Aspirin")


class DoseLogViewTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.log = DoseLog.objects.create(
            medication=self.med,
            taken_at=timezone.now(),
            was_taken=True
        )

    # List
    def test_list_logs(self):
        url = reverse("doselog-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Create
    def test_create_log(self):
        url = reverse("doselog-list")
        payload = {
            "medication": self.med.id,
            "taken_at": timezone.now().isoformat(),
            "was_taken": True
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_log_invalid(self):
        url = reverse("doselog-list")
        payload = {
            "medication": self.med.id,
            "taken_at": "invalid-date",
            "was_taken": True
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Retrieve
    def test_retrieve_log(self):
        url = reverse("doselog-detail", args=[self.log.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Update
    def test_update_log(self):
        url = reverse("doselog-detail", args=[self.log.id])
        payload = {
            "medication": self.med.id,
            "taken_at": timezone.now().isoformat(),
            "was_taken": False
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["was_taken"], False)

    # Delete
    def test_delete_log(self):
        url = reverse("doselog-detail", args=[self.log.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Filter by date
    def test_filter_logs_valid_dates(self):
        url = reverse("doselog-filter-by-date")
        start = (timezone.now() - timedelta(days=1)).date().isoformat()
        end = timezone.now().date().isoformat()

        response = self.client.get(f"{url}?start={start}&end={end}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_logs_missing_dates(self):
        url = reverse("doselog-filter-by-date")

        response = self.client.get(f"{url}?start=&end=")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)