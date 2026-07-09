from django.contrib import admin
from django.utils import timezone
from audit.services import log_event
from .models import ApplicantDocument

@admin.register(ApplicantDocument)
class ApplicantDocumentAdmin(admin.ModelAdmin):
    list_display = ("applicant", "document_type", "review_status", "is_sensitive", "original_filename", "size", "uploaded_at", "reviewed_at")
    list_filter = ("document_type", "review_status", "is_sensitive")
    search_fields = ("applicant__full_name", "original_filename")
    readonly_fields = ("checksum_sha256", "size", "mime_type", "uploaded_at", "reviewed_at")
    actions = ("accept_documents", "reject_documents")

    def _review_documents(self, request, queryset, status):
        reviewed_at = timezone.now()
        for document in queryset.select_related("applicant", "applicant__organization"):
            document.review_status = status
            document.reviewed_by = request.user
            document.reviewed_at = reviewed_at
            document.save(update_fields=["review_status", "reviewed_by", "reviewed_at"])
            log_event(
                document.applicant.organization,
                request.user,
                "document.reviewed",
                "ApplicantDocument",
                str(document.id),
                {"document_type": document.document_type, "review_status": status},
            )

    @admin.action(description="Accept selected documents")
    def accept_documents(self, request, queryset):
        self._review_documents(request, queryset, ApplicantDocument.ReviewStatuses.ACCEPTED)

    @admin.action(description="Reject selected documents")
    def reject_documents(self, request, queryset):
        self._review_documents(request, queryset, ApplicantDocument.ReviewStatuses.REJECTED)
