from .models import AuditLog

def log_event(organization, actor, action, entity_type, entity_id, metadata=None):
    if not organization:
        return None
    return AuditLog.objects.create(
        organization=organization,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {},
    )
