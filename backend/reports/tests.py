from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from applicants.models import Applicant, ConsentRecord, Review
from audit.models import AuditLog
from documents.models import ApplicantDocument
from organizations.models import Organization
from verification.models import VerificationRequest

from .models import ReportRecord


def collect_streaming_response(response):
    return b"".join(response.streaming_content)


class ApplicantReportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.organization = Organization.objects.create(name="Demo Reports Org")
        self.other_organization = Organization.objects.create(name="Other Reports Org")
        self.user = User.objects.create_user(
            username="reporter",
            password="ChangeMe123!",
            organization=self.organization,
            role="reviewer",
        )
        self.applicant = Applicant.objects.create(
            organization=self.organization,
            applicant_type=Applicant.ApplicantTypes.TENANT,
            full_name="Ada Report",
            phone="+2340000000000",
            email="ada@example.test",
            address="Demo address",
            nin_masked="123****8901",
            nin_hash="fake-hash-for-12345678901",
            bvn_masked="222****3333",
            bvn_hash="fake-bvn-hash",
            guarantor_name="Demo Guarantor",
            guarantor_phone="+2340000000001",
            guarantor_relationship="Sibling",
        )
        self.other_applicant = Applicant.objects.create(
            organization=self.other_organization,
            applicant_type=Applicant.ApplicantTypes.CUSTOMER,
            full_name="Other Report",
            phone="+2340000000099",
            nin_masked="999****0000",
            nin_hash="other-hash",
        )
        ConsentRecord.objects.create(
            applicant=self.applicant,
            consent_text="Demo applicant consent text.",
            consent_version="v2",
            accepted=True,
        )
        ApplicantDocument.objects.create(
            applicant=self.applicant,
            document_type=ApplicantDocument.DocumentTypes.ID_CARD,
            original_filename="demo-id.pdf",
            mime_type="application/pdf",
            size=200,
            review_status=ApplicantDocument.ReviewStatuses.ACCEPTED,
            review_note="Accepted demo document.",
        )
        VerificationRequest.objects.create(
            applicant=self.applicant,
            provider="mock",
            verification_type=VerificationRequest.VerificationTypes.NIN,
            status=VerificationRequest.Statuses.VERIFIED,
            response_summary={
                "message": "Mock verification matched 12345678901",
                "nin": "12345678901",
            },
        )
        Review.objects.create(
            applicant=self.applicant,
            reviewer=self.user,
            status=Applicant.Statuses.APPROVED,
            note="Approved for the demo.",
        )

    def test_pdf_endpoint_requires_login(self):
        response = self.client.get(
            reverse("applicant_report_pdf", kwargs={"applicant_id": self.applicant.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_cross_organization_report_download_is_blocked(self):
        self.client.login(username="reporter", password="ChangeMe123!")

        response = self.client.get(
            reverse("applicant_report_pdf", kwargs={"applicant_id": self.other_applicant.id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ReportRecord.objects.count(), 0)

    def test_report_download_creates_record_audit_and_safe_filename(self):
        self.client.login(username="reporter", password="ChangeMe123!")

        response = self.client.get(
            reverse("applicant_report_pdf", kwargs={"applicant_id": self.applicant.id})
        )
        pdf_bytes = collect_streaming_response(response)
        content = pdf_bytes.decode("latin-1", errors="ignore")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertIn(
            "verifyflow-demo-reports-org-ada-report-",
            response["Content-Disposition"],
        )
        report_record = ReportRecord.objects.get()
        self.assertEqual(report_record.applicant, self.applicant)
        self.assertEqual(report_record.generated_by, self.user)
        self.assertEqual(report_record.status, ReportRecord.Statuses.GENERATED)
        self.assertEqual(len(report_record.checksum_sha256), 64)
        self.assertTrue(
            AuditLog.objects.filter(
                action="report.downloaded",
                entity_type="ReportRecord",
                entity_id=str(report_record.id),
            ).exists()
        )
        self.assertIn("123****8901", content)
        self.assertIn("222****3333", content)
        self.assertIn("Consent version", content)
        self.assertIn("Document Checklist", content)
        self.assertIn("Verification History", content)
        self.assertIn("Demo / Not Government Verification", content)
        self.assertNotIn("12345678901", content)
