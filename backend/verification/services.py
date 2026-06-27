import uuid
from .models import VerificationRequest

class MockVerificationProvider:
    provider_name = "mock"

    def verify(self, applicant, verification_type):
        seed = str(applicant.id)[-1]
        status = VerificationRequest.Statuses.VERIFIED if seed in "02468abcdef" else VerificationRequest.Statuses.FAILED
        return {
            "provider": self.provider_name,
            "status": status,
            "request_reference": f"mock-{uuid.uuid4()}",
            "summary": {
                "message": "Mock verification result. Replace with real provider integration later.",
                "applicant": applicant.full_name,
                "verification_type": verification_type,
                "matched": status == VerificationRequest.Statuses.VERIFIED,
            },
        }

def run_mock_verification_for_applicant(applicant, verification_type=VerificationRequest.VerificationTypes.NIN):
    provider = MockVerificationProvider()
    result = provider.verify(applicant, verification_type)
    return VerificationRequest.objects.create(
        applicant=applicant,
        provider=result["provider"],
        verification_type=verification_type,
        status=result["status"],
        request_reference=result["request_reference"],
        response_summary=result["summary"],
    )
