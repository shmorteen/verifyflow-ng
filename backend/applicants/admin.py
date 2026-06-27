from django.contrib import admin
from .models import Applicant, ConsentRecord, Review

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ("full_name", "organization", "applicant_type", "display_identifier", "status", "submitted_at")
    list_filter = ("status", "applicant_type", "organization")
    search_fields = ("full_name", "phone", "email", "nin_masked", "bvn_masked")
    readonly_fields = ("nin_hash", "bvn_hash", "submitted_at", "created_at", "updated_at")

@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("applicant", "accepted", "accepted_at", "consent_version")
    readonly_fields = ("accepted_at", "ip_address", "user_agent")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("applicant", "reviewer", "status", "reviewed_at")
    list_filter = ("status",)
