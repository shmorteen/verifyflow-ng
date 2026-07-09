from django.test import TestCase
from django.urls import reverse

from organizations.models import OnboardingLink, Organization

from .models import ConsentTemplate
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
