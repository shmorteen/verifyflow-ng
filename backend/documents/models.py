import uuid
from django.db import models

def applicant_document_path(instance, filename):
    return f"applicants/{instance.applicant_id}/{instance.document_type}/{filename}"

class ApplicantDocument(models.Model):
    class DocumentTypes(models.TextChoices):
        ID_CARD = "id_card", "ID Card"
        NIN_SLIP = "nin_slip", "NIN Slip"
        PASSPORT = "passport", "Passport"
        UTILITY_BILL = "utility_bill", "Utility Bill"
        SELFIE = "selfie", "Selfie"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey("applicants.Applicant", on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=40, choices=DocumentTypes.choices)
    file = models.FileField(upload_to=applicant_document_path)
    original_filename = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.applicant.full_name} — {self.document_type}"
