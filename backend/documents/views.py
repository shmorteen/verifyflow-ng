from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect

from audit.services import log_event
from applicants.views import ensure_dashboard_access

from .models import ApplicantDocument


def documents_for_user(user):
    documents = ApplicantDocument.objects.select_related("applicant", "applicant__organization")
    if not getattr(user, "organization_id", None):
        return documents.none()
    return documents.filter(applicant__organization=user.organization)


@login_required
def download_document(request, document_id):
    ensure_dashboard_access(request.user)
    document = get_object_or_404(documents_for_user(request.user), id=document_id)
    if not document.file:
        raise Http404("Document file not found.")

    log_event(
        document.applicant.organization,
        request.user,
        "document.viewed",
        "ApplicantDocument",
        str(document.id),
        {"document_type": document.document_type},
    )
    filename = document.original_filename or Path(document.file.name).name
    return FileResponse(document.file.open("rb"), as_attachment=True, filename=filename)


@login_required
def review_document(request, document_id):
    ensure_dashboard_access(request.user)
    document = get_object_or_404(documents_for_user(request.user), id=document_id)
    if request.method != "POST":
        return redirect("applicant_detail", applicant_id=document.applicant_id)

    status = request.POST.get("review_status", "")
    if status not in {
        ApplicantDocument.ReviewStatuses.ACCEPTED,
        ApplicantDocument.ReviewStatuses.REJECTED,
    }:
        messages.error(request, "Choose a valid document review status.")
        return redirect("applicant_detail", applicant_id=document.applicant_id)

    document.mark_reviewed(status, request.user, request.POST.get("review_note", ""))
    log_event(
        document.applicant.organization,
        request.user,
        "document.reviewed",
        "ApplicantDocument",
        str(document.id),
        {"document_type": document.document_type, "review_status": document.review_status},
    )
    messages.success(request, "Document review updated.")
    return redirect("applicant_detail", applicant_id=document.applicant_id)
