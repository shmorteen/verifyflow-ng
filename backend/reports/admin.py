from django.contrib import admin

from .models import ReportRecord


@admin.register(ReportRecord)
class ReportRecordAdmin(admin.ModelAdmin):
    list_display = ("report_reference", "applicant", "report_type", "status", "generated_by", "generated_at")
    list_filter = ("report_type", "status", "generated_at")
    search_fields = ("report_reference", "applicant__full_name", "applicant__organization__name")
    readonly_fields = ("report_reference", "generated_at", "checksum_sha256")
