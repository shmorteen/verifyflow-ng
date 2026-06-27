from django.contrib import admin
from .models import ApplicantDocument

@admin.register(ApplicantDocument)
class ApplicantDocumentAdmin(admin.ModelAdmin):
    list_display = ("applicant", "document_type", "original_filename", "size", "uploaded_at")
    list_filter = ("document_type",)
    search_fields = ("applicant__full_name", "original_filename")
