from django.contrib import admin
from .models import VerificationRequest

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ("applicant", "provider", "verification_type", "status", "created_at")
    list_filter = ("provider", "verification_type", "status")
    search_fields = ("applicant__full_name", "request_reference")
