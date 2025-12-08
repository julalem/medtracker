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
