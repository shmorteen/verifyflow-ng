import uuid
import hashlib
from django.conf import settings
from django.db import models
from django.utils import timezone

def applicant_document_path(instance, filename):
    return f"applicants/{instance.applicant_id}/{instance.document_type}/{filename}"

def file_checksum_sha256(file_obj):
    digest = hashlib.sha256()
    position = None
    try:
        position = file_obj.tell()
    except (AttributeError, OSError):
        position = None
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass

    if hasattr(file_obj, "chunks"):
        for chunk in file_obj.chunks():
            digest.update(chunk)
    else:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)

    if position is not None:
        try:
            file_obj.seek(position)
        except (AttributeError, OSError):
            pass
    return digest.hexdigest()

class ApplicantDocument(models.Model):
    class DocumentTypes(models.TextChoices):
        ID_CARD = "id_card", "ID Card"
        NIN_SLIP = "nin_slip", "NIN Slip"
        PASSPORT = "passport", "Passport"
        UTILITY_BILL = "utility_bill", "Utility Bill"
        SELFIE = "selfie", "Selfie"
        OTHER = "other", "Other"

    class ReviewStatuses(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey("applicants.Applicant", on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=40, choices=DocumentTypes.choices)
    file = models.FileField(upload_to=applicant_document_path)
    original_filename = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    review_status = models.CharField(max_length=20, choices=ReviewStatuses.choices, default=ReviewStatuses.PENDING)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_documents")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_sensitive = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        should_hash_file = update_fields is None or "file" in update_fields or "checksum_sha256" in update_fields
        if self.file and should_hash_file:
            if not self.size:
                self.size = getattr(self.file, "size", 0) or 0
            self.checksum_sha256 = file_checksum_sha256(self.file)
        super().save(*args, **kwargs)

    def mark_reviewed(self, status, reviewer, note=""):
        self.review_status = status
        self.review_note = note or ""
        self.reviewed_by = reviewer if getattr(reviewer, "is_authenticated", False) else None
        self.reviewed_at = timezone.now()
        self.save(update_fields=["review_status", "review_note", "reviewed_by", "reviewed_at"])

    def __str__(self):
        return f"{self.applicant.full_name} - {self.document_type}"
