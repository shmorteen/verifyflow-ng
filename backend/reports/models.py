import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def report_file_path(instance, filename):
    return f"reports/{instance.applicant_id}/{filename}"


def generate_report_reference():
    return f"VF-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:10].upper()}"


class ReportRecord(models.Model):
    class ReportTypes(models.TextChoices):
        APPLICANT_ONBOARDING = "applicant_onboarding", "Applicant onboarding"

    class Statuses(models.TextChoices):
        GENERATED = "generated", "Generated"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_reference = models.CharField(max_length=40, unique=True, default=generate_report_reference)
    applicant = models.ForeignKey("applicants.Applicant", on_delete=models.CASCADE, related_name="report_records")
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_reports")
    generated_at = models.DateTimeField(default=timezone.now)
    report_type = models.CharField(max_length=40, choices=ReportTypes.choices, default=ReportTypes.APPLICANT_ONBOARDING)
    file = models.FileField(upload_to=report_file_path, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=Statuses.choices, default=Statuses.GENERATED)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.report_reference} - {self.applicant.full_name}"
