import hashlib
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from applicants.models import Applicant
from audit.models import AuditLog
from organizations.models import OnboardingLink, Organization

from .models import ApplicantDocument

PDF_BYTES = b"%PDF-1.4\n% fake pdf for tests\n"
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"fake jpeg bytes"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake png bytes"


class ApplicantDocumentUploadTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_root,
            MAX_UPLOAD_SIZE_BYTES=1024,
        )
        self.settings_override.enable()
        self.organization = Organization.objects.create(name="Demo Document Org")
        self.onboarding_link = OnboardingLink.objects.create(
            organization=self.organization,
            applicant_type_default="tenant",
        )

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def onboarding_url(self):
        return reverse(
            "onboarding_form",
            kwargs={
                "organization_slug": self.organization.slug,
                "token": self.onboarding_link.token,
            },
        )

    def post_onboarding(self, uploaded_file):
        return self.client.post(
            self.onboarding_url(),
            {
                "applicant_type": "tenant",
                "full_name": "Demo Applicant",
                "phone": "+2340000000000",
                "nin": "12345678901",
                "id_document_type": ApplicantDocument.DocumentTypes.ID_CARD,
                "id_document": uploaded_file,
                "consent": "on",
            },
        )

    def test_valid_pdf_jpeg_and_png_uploads(self):
        valid_files = [
            ("demo.pdf", PDF_BYTES, "application/pdf"),
            ("demo.jpg", JPEG_BYTES, "image/jpeg"),
            ("demo.jpeg", JPEG_BYTES, "image/jpeg"),
            ("demo.png", PNG_BYTES, "image/png"),
        ]

        for filename, content, content_type in valid_files:
            with self.subTest(filename=filename):
                response = self.post_onboarding(
                    SimpleUploadedFile(filename, content, content_type=content_type)
                )

                self.assertEqual(response.status_code, 200)
                document = ApplicantDocument.objects.get(original_filename=filename)
                self.assertEqual(document.original_filename, filename)
                self.assertEqual(document.review_status, ApplicantDocument.ReviewStatuses.PENDING)
                self.assertEqual(document.checksum_sha256, hashlib.sha256(content).hexdigest())

    def test_invalid_file_extension_is_rejected(self):
        response = self.post_onboarding(
            SimpleUploadedFile(
                "payload.exe",
                b"MZ fake executable",
                content_type="application/x-msdownload",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsupported file type")
        self.assertEqual(Applicant.objects.count(), 0)
        self.assertEqual(ApplicantDocument.objects.count(), 0)

    def test_mime_type_mismatch_is_rejected(self):
        response = self.post_onboarding(
            SimpleUploadedFile(
                "document.pdf",
                PDF_BYTES,
                content_type="image/png",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "content type does not match")
        self.assertEqual(Applicant.objects.count(), 0)
        self.assertEqual(ApplicantDocument.objects.count(), 0)

    def test_oversized_file_is_rejected(self):
        with override_settings(MAX_UPLOAD_SIZE_BYTES=8):
            response = self.post_onboarding(
                SimpleUploadedFile(
                    "large.pdf",
                    PDF_BYTES + b"x" * 32,
                    content_type="application/pdf",
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File is too large")
        self.assertEqual(Applicant.objects.count(), 0)
        self.assertEqual(ApplicantDocument.objects.count(), 0)

    def test_upload_creates_document_audit_log(self):
        self.post_onboarding(
            SimpleUploadedFile("demo.pdf", PDF_BYTES, content_type="application/pdf")
        )

        document = ApplicantDocument.objects.get()
        self.assertTrue(
            AuditLog.objects.filter(
                action="document.uploaded",
                entity_type="ApplicantDocument",
                entity_id=str(document.id),
            ).exists()
        )


class ApplicantDocumentReviewTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        self.organization = Organization.objects.create(name="Demo Review Org")
        self.applicant = Applicant.objects.create(
            organization=self.organization,
            applicant_type=Applicant.ApplicantTypes.TENANT,
            full_name="Demo Reviewer Applicant",
            phone="+2340000000000",
            nin_masked="123****8901",
            nin_hash="fake-hash",
        )
        self.document = ApplicantDocument.objects.create(
            applicant=self.applicant,
            document_type=ApplicantDocument.DocumentTypes.ID_CARD,
            file=SimpleUploadedFile("demo.pdf", PDF_BYTES, content_type="application/pdf"),
            original_filename="demo.pdf",
            mime_type="application/pdf",
            size=len(PDF_BYTES),
        )
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            password="ChangeMe123!",
            organization=self.organization,
            role="reviewer",
        )
        self.client.login(username="reviewer", password="ChangeMe123!")

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_checksum_is_generated_when_document_is_saved(self):
        self.assertEqual(
            self.document.checksum_sha256,
            hashlib.sha256(PDF_BYTES).hexdigest(),
        )

    def test_document_review_status_update_creates_audit_log(self):
        response = self.client.post(
            reverse("review_document", kwargs={"document_id": self.document.id}),
            {
                "review_status": ApplicantDocument.ReviewStatuses.ACCEPTED,
                "review_note": "Fake document looks clear.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.document.refresh_from_db()
        self.assertEqual(self.document.review_status, ApplicantDocument.ReviewStatuses.ACCEPTED)
        self.assertEqual(self.document.review_note, "Fake document looks clear.")
        self.assertEqual(self.document.reviewed_by, self.user)
        self.assertIsNotNone(self.document.reviewed_at)
        self.assertTrue(
            AuditLog.objects.filter(
                action="document.reviewed",
                entity_type="ApplicantDocument",
                entity_id=str(self.document.id),
            ).exists()
        )

    def test_document_download_creates_audit_log(self):
        response = self.client.get(
            reverse("download_document", kwargs={"document_id": self.document.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="document.viewed",
                entity_type="ApplicantDocument",
                entity_id=str(self.document.id),
            ).exists()
        )
