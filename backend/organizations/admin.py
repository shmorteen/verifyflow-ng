from django.contrib import admin
from .models import Organization, OnboardingLink

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "business_type", "contact_email", "created_at")
    search_fields = ("name", "slug", "contact_email")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(OnboardingLink)
class OnboardingLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "organization", "token", "is_active", "created_at")
    list_filter = ("is_active", "organization")
