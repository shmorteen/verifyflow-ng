from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "organization", "actor", "created_at")
    list_filter = ("action", "organization")
    search_fields = ("action", "entity_type", "entity_id")
    readonly_fields = ("created_at",)
