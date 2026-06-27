import uuid
from django.db import models

class VerificationRequest(models.Model):
    class VerificationTypes(models.TextChoices):
        NIN = "nin", "NIN"
        BVN = "bvn", "BVN"
        FACE_MATCH = "face_match", "Face Match"
        DOCUMENT_CHECK = "document_check", "Document Check"

    class Statuses(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey("applicants.Applicant", on_delete=models.CASCADE, related_name="verification_requests")
    provider = models.CharField(max_length=80, default="mock")
    verification_type = models.CharField(max_length=40, choices=VerificationTypes.choices)
    status = models.CharField(max_length=30, choices=Statuses.choices, default=Statuses.NOT_STARTED)
    request_reference = models.CharField(max_length=120, blank=True)
    response_summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
