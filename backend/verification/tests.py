from django.test import TestCase
from applicants.models import Applicant
from organizations.models import Organization
from verification.services import run_mock_verification_for_applicant

class MockVerificationTests(TestCase):
    def test_mock_verification_creates_request(self):
        org = Organization.objects.create(name="Test Org")
        applicant = Applicant.objects.create(organization=org, full_name="Test Applicant", phone="+2340000000000", nin_masked="123****8901", nin_hash="fakehash")
        verification = run_mock_verification_for_applicant(applicant)
        self.assertEqual(verification.provider, "mock")
        self.assertTrue(verification.request_reference.startswith("mock-"))
