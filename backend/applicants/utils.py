import hashlib

def mask_identity_number(value: str) -> str:
    clean = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(clean) < 7:
        return ""
    return f"{clean[:3]}****{clean[-4:]}"

def hash_sensitive_value(value: str) -> str:
    clean = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not clean:
        return ""
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()

def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
