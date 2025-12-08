from unittest.mock import patch

from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_adherence_rate_no_doses(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        adherence = med.adherence_rate()
        self.assertEqual(adherence, 0.0)

    def test_adherence_rate_half_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now)

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_adherence_rate_invalid_prescribed_per_day(self):
        med = Medication.objects.create(name="TestMed", dosage_mg=50, prescribed_per_day=0)
        adherence = med.adherence_rate()
        self.assertEqual(adherence, 0.0)

    def test_adherence_rate_more_than_expected(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now)
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

class DoseLogModelTests(TestCase):

    def test_create_valid_doselog(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        now = timezone.now()
        log = DoseLog.objects.create(medication=med, taken_at=now)

        self.assertEqual(log.medication, med)
        self.assertEqual(log.taken_at, now)

    def test_doselog_missing_taken_at(self):
        med = Medication.objects.create(name="TestMed", dosage_mg=50, prescribed_per_day=1)
        with self.assertRaises(Exception):
            DoseLog.objects.create(medication=med, taken_at=None)

    def test_expected_doses_valid(self):
        med = Medication.objects.create(name="A", dosage_mg=10, prescribed_per_day=2)
        self.assertEqual(med.expected_doses(3), 6)

    def test_expected_doses_negative_days(self):
        med = Medication.objects.create(name="A", dosage_mg=10, prescribed_per_day=2)
        with self.assertRaises(ValueError):
            med.expected_doses(-1)

    def test_expected_doses_zero_prescribed_per_day(self):
        med = Medication.objects.create(name="A", dosage_mg=10, prescribed_per_day=0)
        with self.assertRaises(ValueError):
            med.expected_doses(5)

    def test_adherence_over_period_valid(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)

        now = timezone.now()
        today = now.date()

        DoseLog.objects.create(medication=med, taken_at=now, was_taken=True)

        adherence = med.adherence_rate_over_period(today, today)
        self.assertEqual(adherence, 100.0)

    def test_adherence_over_period_no_expected_doses(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=0)

        today = timezone.now().date()

        with self.assertRaises(ValueError):
            med.adherence_rate_over_period(today, today)

    def test_adherence_over_period_invalid_date_order(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        with self.assertRaises(ValueError):
            med.adherence_rate_over_period(today, yesterday)

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_success(self, mock_api):
        mock_api.return_value = {"name": "Aspirin"}
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)

        result = med.fetch_external_info()
        self.assertEqual(result, {"name": "Aspirin"})

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_error(self, mock_api):
        mock_api.side_effect = Exception("API failed")
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)

        result = med.fetch_external_info()
        self.assertEqual(result, {"error": "API failed"})

    class DoseLogStringTests(TestCase):

        def test_doselog_str_format(self):
            med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
            timestamp = timezone.now()
            log = DoseLog.objects.create(medication=med, taken_at=timestamp, was_taken=True)

            result = str(log)
            self.assertIn("Aspirin", result)
            self.assertIn("Taken", result)
            self.assertIn(timestamp.strftime("%Y-%m-%d"), result)
