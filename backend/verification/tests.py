from django.test import TestCase, override_settings

from applicants.models import Applicant
from organizations.models import Organization
from verification.models import VerificationRequest
from verification.providers import (
    DojahProvider,
    KYCProvider,
    MockVerificationProvider,
    ProviderResult,
    SmileIDProvider,
)
from verification.services import (
    run_mock_verification_for_applicant,
    run_verification_for_applicant,
)


class LeakyProvider(KYCProvider):
    provider_name = "test"

    def verify_nin(self, applicant):
        return ProviderResult(
            reference="safe-reference",
            status=VerificationRequest.Statuses.VERIFIED,
            response_summary={
                "nin": "12345678901",
                "message": "Matched identity 12345678901",
            },
        )

    def verify_bvn(self, applicant):
        raise RuntimeError("Provider rejected BVN 10987654321")

    def verify_document(self, applicant):
        return ProviderResult()

    def verify_face_match(self, applicant):
        return ProviderResult()


class KYCProviderTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(name="Test Org")
        self.applicant = Applicant.objects.create(
            organization=organization,
            full_name="Demo Applicant",
            phone="+2340000000000",
            nin_masked="123****8901",
            nin_hash="fakehash",
        )

    def test_mock_provider_supports_every_verification_method(self):
        provider = MockVerificationProvider()
        methods = [
            provider.verify_nin,
            provider.verify_bvn,
            provider.verify_document,
            provider.verify_face_match,
        ]

        for method in methods:
            with self.subTest(method=method.__name__):
                result = method(self.applicant)
                self.assertTrue(result.reference.startswith("mock-"))
                self.assertIn(
                    result.status,
                    [
                        VerificationRequest.Statuses.VERIFIED,
                        VerificationRequest.Statuses.FAILED,
                    ],
                )

    def test_mock_verification_creates_minimal_request(self):
        verification = run_mock_verification_for_applicant(self.applicant)

        self.assertEqual(verification.provider, "mock")
        self.assertTrue(verification.request_reference.startswith("mock-"))
        self.assertNotIn(self.applicant.full_name, str(verification.response_summary))

    def test_service_dispatches_each_verification_type(self):
        for verification_type in VerificationRequest.VerificationTypes.values:
            with self.subTest(verification_type=verification_type):
                verification = run_verification_for_applicant(
                    self.applicant,
                    verification_type,
                    MockVerificationProvider(),
                )
                self.assertEqual(verification.verification_type, verification_type)

    def test_sensitive_numbers_are_redacted_from_summary_and_errors(self):
        nin_result = run_verification_for_applicant(
            self.applicant,
            VerificationRequest.VerificationTypes.NIN,
            LeakyProvider(),
        )
        bvn_result = run_verification_for_applicant(
            self.applicant,
            VerificationRequest.VerificationTypes.BVN,
            LeakyProvider(),
        )

        self.assertNotIn("12345678901", str(nin_result.response_summary))
        self.assertEqual(nin_result.response_summary["nin"], "[REDACTED]")
        self.assertNotIn("10987654321", bvn_result.error_message)
        self.assertIn("[REDACTED ID]", bvn_result.error_message)

    @override_settings(DOJAH_API_KEY="", SMILE_ID_API_KEY="")
    def test_placeholder_providers_do_not_require_credentials(self):
        providers = [DojahProvider(), SmileIDProvider()]

        for provider in providers:
            with self.subTest(provider=provider.provider_name):
                result = provider.verify_nin(self.applicant)
                self.assertEqual(result.status, VerificationRequest.Statuses.ERROR)
                self.assertEqual(
                    result.error_message,
                    "Provider API key is not configured.",
                )
