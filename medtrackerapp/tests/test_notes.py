from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from medtrackerapp.models import Medication, Note


class NotesAPITests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(
            name="TestMed",
            description="",
            prescribed_per_day=2,
        )
        self.notes_url = reverse("note-list")

    def test_create_note_success(self):
        payload = {
            "medication": self.med.id,
            "text": "Patient reported mild side effects."
        }
        response = self.client.post(self.notes_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(response.data["text"], payload["text"])

    def test_create_note_missing_text_returns_400(self):
        payload = {"medication": self.med.id}
        response = self.client.post(self.notes_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_notes(self):
        Note.objects.create(medication=self.med, text="Note A")
        Note.objects.create(medication=self.med, text="Note B")

        response = self.client.get(self.notes_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_single_note(self):
        note = Note.objects.create(medication=self.med, text="Detailed note")

        url = reverse("note-detail", args=[note.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], note.text)

    def test_delete_note(self):
        note = Note.objects.create(medication=self.med, text="To be deleted")

        url = reverse("note-detail", args=[note.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Note.objects.count(), 0)

    def test_update_note_not_allowed(self):
        note = Note.objects.create(medication=self.med, text="Original")

        url = reverse("note-detail", args=[note.id])
        response = self.client.put(url, {"text": "Updated"})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
