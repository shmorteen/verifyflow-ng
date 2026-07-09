from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_UPLOADS = {
    ".pdf": {
        "mime_types": {"application/pdf"},
        "signature": lambda header: header.startswith(b"%PDF-"),
    },
    ".jpg": {
        "mime_types": {"image/jpeg"},
        "signature": lambda header: header.startswith(b"\xff\xd8\xff"),
    },
    ".jpeg": {
        "mime_types": {"image/jpeg"},
        "signature": lambda header: header.startswith(b"\xff\xd8\xff"),
    },
    ".png": {
        "mime_types": {"image/png"},
        "signature": lambda header: header.startswith(b"\x89PNG\r\n\x1a\n"),
    },
}

BLOCKED_EXTENSIONS = {
    ".7z",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".gz",
    ".js",
    ".msi",
    ".php",
    ".ps1",
    ".py",
    ".rar",
    ".scr",
    ".sh",
    ".tar",
    ".zip",
}

ALLOWED_FILE_TYPES_TEXT = "PDF, JPG, JPEG, or PNG"


def format_file_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.0f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes} bytes"


def read_header(uploaded_file, length=16):
    position = None
    try:
        position = uploaded_file.tell()
    except (AttributeError, OSError):
        position = None
    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(length)
    finally:
        if position is not None:
            try:
                uploaded_file.seek(position)
            except (AttributeError, OSError):
                pass
    return header


def validate_uploaded_document(uploaded_file):
    if not uploaded_file:
        return uploaded_file

    max_size = settings.MAX_UPLOAD_SIZE_BYTES
    if uploaded_file.size > max_size:
        raise ValidationError(
            f"File is too large. Maximum upload size is {format_file_size(max_size)}.",
            code="file_too_large",
        )

    extension = Path(uploaded_file.name).suffix.lower()
    if extension in BLOCKED_EXTENSIONS or extension not in ALLOWED_UPLOADS:
        raise ValidationError(
            f"Unsupported file type. Upload a {ALLOWED_FILE_TYPES_TEXT} file.",
            code="unsupported_file_type",
        )

    content_type = (getattr(uploaded_file, "content_type", "") or "").split(";")[0].strip().lower()
    allowed = ALLOWED_UPLOADS[extension]
    if content_type not in allowed["mime_types"]:
        raise ValidationError(
            f"The file content type does not match the extension. Upload a valid {ALLOWED_FILE_TYPES_TEXT} file.",
            code="mime_type_mismatch",
        )

    if not allowed["signature"](read_header(uploaded_file)):
        raise ValidationError(
            f"The file contents do not look like a valid {ALLOWED_FILE_TYPES_TEXT} file.",
            code="invalid_file_signature",
        )

    return uploaded_file
