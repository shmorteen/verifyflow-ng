import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from django.conf import settings

from .models import VerificationRequest


IDENTITY_NUMBER_PATTERN = re.compile(r"(?<!\d)\d{11}(?!\d)")


@dataclass(frozen=True)
class ProviderResult:
    reference: str = ""
    status: str = VerificationRequest.Statuses.ERROR
    response_summary: dict = field(default_factory=dict)
    error_message: str = ""


class KYCProvider(ABC):
    provider_name = ""

    @abstractmethod
    def verify_nin(self, applicant):
        raise NotImplementedError

    @abstractmethod
    def verify_bvn(self, applicant):
        raise NotImplementedError

    @abstractmethod
    def verify_document(self, applicant):
        raise NotImplementedError

    @abstractmethod
    def verify_face_match(self, applicant):
        raise NotImplementedError


class MockVerificationProvider(KYCProvider):
    provider_name = "mock"

    def _verify(self, applicant, verification_type):
        seed = str(applicant.id)[-1]
        status = (
            VerificationRequest.Statuses.VERIFIED
            if seed in "02468abcdef"
            else VerificationRequest.Statuses.FAILED
        )
        return ProviderResult(
            reference=f"mock-{uuid.uuid4()}",
            status=status,
            response_summary={
                "message": "Demo verification completed by the mock provider.",
                "verification_type": verification_type,
                "matched": status == VerificationRequest.Statuses.VERIFIED,
            },
        )

    def verify_nin(self, applicant):
        return self._verify(applicant, VerificationRequest.VerificationTypes.NIN)

    def verify_bvn(self, applicant):
        return self._verify(applicant, VerificationRequest.VerificationTypes.BVN)

    def verify_document(self, applicant):
        return self._verify(
            applicant, VerificationRequest.VerificationTypes.DOCUMENT_CHECK
        )

    def verify_face_match(self, applicant):
        return self._verify(
            applicant, VerificationRequest.VerificationTypes.FACE_MATCH
        )


class UnavailableProvider(KYCProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def _unavailable(self, verification_type):
        reason = (
            "Provider API key is not configured."
            if not self.api_key
            else "Provider adapter is a placeholder and is not enabled."
        )
        return ProviderResult(
            status=VerificationRequest.Statuses.ERROR,
            response_summary={"verification_type": verification_type},
            error_message=reason,
        )

    def verify_nin(self, applicant):
        return self._unavailable(VerificationRequest.VerificationTypes.NIN)

    def verify_bvn(self, applicant):
        return self._unavailable(VerificationRequest.VerificationTypes.BVN)

    def verify_document(self, applicant):
        return self._unavailable(
            VerificationRequest.VerificationTypes.DOCUMENT_CHECK
        )

    def verify_face_match(self, applicant):
        return self._unavailable(VerificationRequest.VerificationTypes.FACE_MATCH)


class DojahProvider(UnavailableProvider):
    provider_name = "dojah"

    def __init__(self, api_key=None):
        super().__init__(
            api_key if api_key is not None else settings.DOJAH_API_KEY
        )


class SmileIDProvider(UnavailableProvider):
    provider_name = "smile_id"

    def __init__(self, api_key=None):
        super().__init__(
            api_key if api_key is not None else settings.SMILE_ID_API_KEY
        )


def redact_sensitive_text(value):
    return IDENTITY_NUMBER_PATTERN.sub("[REDACTED ID]", str(value))


def sanitize_response_summary(value):
    sensitive_keys = {"nin", "bvn", "nin_number", "bvn_number", "identity_number"}
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if str(key).lower() in sensitive_keys
                else sanitize_response_summary(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_response_summary(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_response_summary(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value
