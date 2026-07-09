from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from audit.models import AuditLog
from documents.models import ApplicantDocument
from organizations.models import OnboardingLink, Organization
from verification.models import VerificationRequest

from .models import Applicant, ConsentTemplate
from .utils import hash_sensitive_value, mask_identity_number

class IdentityUtilsTests(TestCase):
    def test_mask_identity_number(self):
        self.assertEqual(mask_identity_number("12345678901"), "123****8901")

    def test_hash_sensitive_value_is_stable(self):
        self.assertEqual(hash_sensitive_value("12345678901"), hash_sensitive_value("12345678901"))
        self.assertNotEqual(hash_sensitive_value("12345678901"), hash_sensitive_value("12345678902"))


class ConsentTemplateTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(name="Demo Consent Org")
        self.onboarding_link = OnboardingLink.objects.create(
            organization=organization,
            applicant_type_default="tenant",
        )
        self.template = ConsentTemplate.objects.create(
            version="v2",
            title="Applicant consent",
            body="I consent to this fake onboarding test.",
            is_active=True,
        )

    def test_submission_preserves_consent_version_and_text(self):
        response = self.client.post(
            reverse(
                "onboarding_form",
                kwargs={
                    "organization_slug": self.onboarding_link.organization.slug,
                    "token": self.onboarding_link.token,
                },
            ),
            {
                "applicant_type": "tenant",
                "full_name": "Demo Applicant",
                "phone": "+2340000000000",
                "nin": "12345678901",
                "consent": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        consent_record = self.onboarding_link.applicants.get().consent
        self.assertEqual(consent_record.consent_version, "v2")
        self.assertEqual(
            consent_record.consent_text,
            "I consent to this fake onboarding test.",
        )

        self.template.version = "v3"
        self.template.body = "Updated consent text for future applicants."
        self.template.save()
        consent_record.refresh_from_db()

        self.assertEqual(consent_record.consent_version, "v2")
        self.assertEqual(
            consent_record.consent_text,
            "I consent to this fake onboarding test.",
        )


class DashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.org = Organization.objects.create(name="Dashboard Demo Org")
        self.other_org = Organization.objects.create(name="Other Demo Org")
        self.owner = User.objects.create_user(
            username="owner",
            password="ChangeMe123!",
            organization=self.org,
            role="owner",
        )
        self.admin = User.objects.create_user(
            username="admin",
            password="ChangeMe123!",
            organization=self.org,
            role="admin",
        )
        self.reviewer = User.objects.create_user(
            username="reviewer",
            password="ChangeMe123!",
            organization=self.org,
            role="reviewer",
        )
        self.blocked_user = User.objects.create_user(
            username="blocked",
            password="ChangeMe123!",
            organization=self.org,
            role="blocked",
        )
        self.applicant = Applicant.objects.create(
            organization=self.org,
            applicant_type=Applicant.ApplicantTypes.TENANT,
            full_name="Ada Demo",
            phone="+2340000000001",
            email="ada@example.test",
            nin_masked="123****8901",
            nin_hash="fake-nin-hash",
            bvn_masked="222****3333",
            status=Applicant.Statuses.PENDING,
        )
        self.other_applicant = Applicant.objects.create(
            organization=self.other_org,
            applicant_type=Applicant.ApplicantTypes.EMPLOYEE,
            full_name="Other Org Applicant",
            phone="+2340000000099",
            email="other@example.test",
            nin_masked="999****0000",
            nin_hash="other-hash",
            status=Applicant.Statuses.PENDING,
        )
        self.document = ApplicantDocument.objects.create(
            applicant=self.applicant,
            document_type=ApplicantDocument.DocumentTypes.ID_CARD,
            original_filename="demo.pdf",
            mime_type="application/pdf",
            size=20,
            review_status=ApplicantDocument.ReviewStatuses.PENDING,
        )
        self.verification = VerificationRequest.objects.create(
            applicant=self.applicant,
            verification_type=VerificationRequest.VerificationTypes.NIN,
            status=VerificationRequest.Statuses.VERIFIED,
        )
        VerificationRequest.objects.create(
            applicant=self.applicant,
            verification_type=VerificationRequest.VerificationTypes.BVN,
            status=VerificationRequest.Statuses.FAILED,
        )

    def login(self, user=None):
        self.client.login(username=(user or self.owner).username, password="ChangeMe123!")

    def test_dashboard_only_shows_user_organization_applicants(self):
        self.login()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada Demo")
        self.assertNotContains(response, "Other Org Applicant")
        self.assertEqual(response.context["summary"]["total"], 1)

    def test_dashboard_search_and_filters(self):
        old_applicant = Applicant.objects.create(
            organization=self.org,
            applicant_type=Applicant.ApplicantTypes.STUDENT,
            full_name="Bola Old",
            phone="+2340000000002",
            email="bola@example.test",
            nin_masked="555****1111",
            status=Applicant.Statuses.REJECTED,
        )
        Applicant.objects.filter(id=old_applicant.id).update(submitted_at=timezone.now() - timedelta(days=7))
        self.login()

        response = self.client.get(reverse("dashboard"), {"q": "123****8901"})
        self.assertContains(response, "Ada Demo")
        self.assertNotContains(response, "Bola Old")

        response = self.client.get(
            reverse("dashboard"),
            {
                "status": Applicant.Statuses.PENDING,
                "applicant_type": Applicant.ApplicantTypes.TENANT,
                "verification_status": VerificationRequest.Statuses.VERIFIED,
                "document_review_status": ApplicantDocument.ReviewStatuses.PENDING,
                "date_from": timezone.now().date().isoformat(),
            },
        )
        self.assertContains(response, "Ada Demo")
        self.assertNotContains(response, "Bola Old")

    def test_dashboard_paginates_applicants(self):
        for index in range(12):
            Applicant.objects.create(
                organization=self.org,
                applicant_type=Applicant.ApplicantTypes.CUSTOMER,
                full_name=f"Paged Applicant {index}",
                phone=f"+23400000010{index:02d}",
                nin_masked=f"100****{index:04d}",
            )
        self.login()

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["applicants"]), 10)
        self.assertTrue(response.context["page_obj"].has_next())

    def test_owner_admin_and_reviewer_can_access_dashboard(self):
        for user in [self.owner, self.admin, self.reviewer]:
            with self.subTest(role=user.role):
                self.client.logout()
                self.login(user)
                response = self.client.get(reverse("dashboard"))
                self.assertEqual(response.status_code, 200)

    def test_non_dashboard_role_is_blocked(self):
        self.login(self.blocked_user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_cross_organization_detail_access_is_blocked(self):
        self.login()

        response = self.client.get(reverse("applicant_detail", kwargs={"applicant_id": self.other_applicant.id}))

        self.assertEqual(response.status_code, 404)

    def test_csv_export_uses_filters_and_masked_identity_values(self):
        self.login()

        response = self.client.get(reverse("export_applicants_csv"), {"q": "Ada"})
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Exported at", content)
        self.assertIn("123****8901", content)
        self.assertNotIn("12345678901", content)
        self.assertNotIn("Other Org Applicant", content)
        self.assertTrue(AuditLog.objects.filter(action="applicant.exported").exists())

    def test_applicant_review_is_audited(self):
        self.login(self.reviewer)

        response = self.client.post(
            reverse("review_applicant", kwargs={"applicant_id": self.applicant.id}),
            {"status": Applicant.Statuses.UNDER_REVIEW, "note": "Starting review."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(AuditLog.objects.filter(action="applicant.reviewed", entity_id=str(self.applicant.id)).exists())

    def test_bulk_status_action_updates_only_user_org_and_is_audited(self):
        self.login()

        response = self.client.post(
            reverse("bulk_applicant_action"),
            {
                "bulk_action": "approve",
                "selected_applicants": [str(self.applicant.id), str(self.other_applicant.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.applicant.refresh_from_db()
        self.other_applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, Applicant.Statuses.APPROVED)
        self.assertEqual(self.other_applicant.status, Applicant.Statuses.PENDING)
        self.assertTrue(AuditLog.objects.filter(action="applicant.bulk_reviewed", entity_id=str(self.applicant.id)).exists())
        self.assertFalse(AuditLog.objects.filter(action="applicant.bulk_reviewed", entity_id=str(self.other_applicant.id)).exists())

    def test_bulk_export_selected_is_audited_and_scoped(self):
        self.login()

        response = self.client.post(
            reverse("bulk_applicant_action"),
            {
                "bulk_action": "export_selected",
                "selected_applicants": [str(self.applicant.id), str(self.other_applicant.id)],
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ada Demo", content)
        self.assertNotIn("Other Org Applicant", content)
        self.assertTrue(AuditLog.objects.filter(action="applicant.bulk_exported").exists())
