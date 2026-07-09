from .models import VerificationRequest
from .providers import (
    MockVerificationProvider,
    ProviderResult,
    redact_sensitive_text,
    sanitize_response_summary,
)


PROVIDER_METHODS = {
    VerificationRequest.VerificationTypes.NIN: "verify_nin",
    VerificationRequest.VerificationTypes.BVN: "verify_bvn",
    VerificationRequest.VerificationTypes.DOCUMENT_CHECK: "verify_document",
    VerificationRequest.VerificationTypes.FACE_MATCH: "verify_face_match",
}


def run_verification_for_applicant(applicant, verification_type, provider):
    method_name = PROVIDER_METHODS.get(verification_type)
    if method_name is None:
        raise ValueError("Unsupported verification type.")

    try:
        result = getattr(provider, method_name)(applicant)
        if not isinstance(result, ProviderResult):
            raise TypeError("Provider returned an invalid result.")
    except Exception as exc:
        result = ProviderResult(
            status=VerificationRequest.Statuses.ERROR,
            error_message=redact_sensitive_text(exc),
        )

    return VerificationRequest.objects.create(
        applicant=applicant,
        provider=provider.provider_name,
        verification_type=verification_type,
        status=result.status,
        request_reference=result.reference,
        response_summary=sanitize_response_summary(result.response_summary),
        error_message=redact_sensitive_text(result.error_message),
    )

def run_mock_verification_for_applicant(applicant, verification_type=VerificationRequest.VerificationTypes.NIN):
    return run_verification_for_applicant(
        applicant,
        verification_type,
        MockVerificationProvider(),
    )
