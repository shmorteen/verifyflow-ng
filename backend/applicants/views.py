import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils import timezone
from audit.services import log_event
from documents.models import ApplicantDocument
from organizations.models import OnboardingLink
from verification.models import VerificationRequest
from .forms import ApplicantOnboardingForm, CONSENT_TEXT, ReviewForm
from .models import Applicant, ConsentRecord, ConsentTemplate, Review
from .utils import get_client_ip, hash_sensitive_value, mask_identity_number

DASHBOARD_ROLES = {"owner", "admin", "reviewer"}
BULK_ACTION_STATUS_MAP = {
    "mark_under_review": Applicant.Statuses.UNDER_REVIEW,
    "approve": Applicant.Statuses.APPROVED,
    "reject": Applicant.Statuses.REJECTED,
}


def ensure_dashboard_access(user):
    if not user.is_authenticated:
        raise PermissionDenied
    if getattr(user, "role", None) not in DASHBOARD_ROLES and not user.is_superuser:
        raise PermissionDenied
    if not user.organization_id:
        raise PermissionDenied

def applicants_for_user(user):
    applicants = Applicant.objects.select_related("organization")
    if not getattr(user, "organization_id", None):
        return applicants.none()
    return applicants.filter(organization=user.organization)


def onboarding_links_for_user(user):
    links = OnboardingLink.objects.filter(is_active=True).select_related("organization").order_by("label")
    if not getattr(user, "organization_id", None):
        return links.none()
    return links.filter(organization=user.organization)


def filter_applicants(queryset, params):
    query = params.get("q", "").strip()
    status = params.get("status", "").strip()
    applicant_type = params.get("applicant_type", "").strip()
    date_from = params.get("date_from", "").strip()
    date_to = params.get("date_to", "").strip()
    verification_status = params.get("verification_status", "").strip()
    document_review_status = params.get("document_review_status", "").strip()

    if query:
        queryset = queryset.filter(
            Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(nin_masked__icontains=query)
            | Q(bvn_masked__icontains=query)
        )
    if status:
        queryset = queryset.filter(status=status)
    if applicant_type:
        queryset = queryset.filter(applicant_type=applicant_type)
    if date_from:
        parsed_date_from = parse_date(date_from)
        if parsed_date_from:
            queryset = queryset.filter(submitted_at__date__gte=parsed_date_from)
    if date_to:
        parsed_date_to = parse_date(date_to)
        if parsed_date_to:
            queryset = queryset.filter(submitted_at__date__lte=parsed_date_to)
    if verification_status:
        queryset = queryset.filter(verification_requests__status=verification_status)
    if document_review_status:
        queryset = queryset.filter(documents__review_status=document_review_status)

    return queryset.distinct().order_by("-submitted_at")


def dashboard_filter_context(params):
    return {
        "query": params.get("q", "").strip(),
        "status": params.get("status", "").strip(),
        "applicant_type": params.get("applicant_type", "").strip(),
        "date_from": params.get("date_from", "").strip(),
        "date_to": params.get("date_to", "").strip(),
        "verification_status": params.get("verification_status", "").strip(),
        "document_review_status": params.get("document_review_status", "").strip(),
    }


def build_csv_response(applicants, organization, actor, action="applicant.exported", selected_count=None):
    exported_at = timezone.now()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="verifyflow_applicants.csv"'
    writer = csv.writer(response)
    writer.writerow(["Exported at", "Full name", "Phone", "Email", "Applicant type", "NIN", "BVN", "Status", "Submitted at"])
    for applicant in applicants:
        writer.writerow([
            exported_at.isoformat(),
            applicant.full_name,
            applicant.phone,
            applicant.email,
            applicant.get_applicant_type_display(),
            applicant.nin_masked,
            applicant.bvn_masked,
            applicant.get_status_display(),
            applicant.submitted_at.isoformat(),
        ])
    log_event(
        organization,
        actor,
        action,
        "Applicant",
        "bulk" if selected_count is not None else "export",
        {"count": selected_count if selected_count is not None else applicants.count(), "exported_at": exported_at.isoformat()},
    )
    return response

def onboarding_form(request, organization_slug, token):
    onboarding_link = get_object_or_404(OnboardingLink, organization__slug=organization_slug, token=token, is_active=True)
    consent_template = ConsentTemplate.objects.filter(is_active=True).first()
    consent_text = consent_template.body if consent_template else CONSENT_TEXT
    consent_version = consent_template.version if consent_template else "v1"
    initial = {"applicant_type": onboarding_link.applicant_type_default}
    form = ApplicantOnboardingForm(
        request.POST or None,
        request.FILES or None,
        initial=initial,
        consent_text=consent_text,
    )
    if request.method == "POST" and form.is_valid():
        applicant = Applicant.objects.create(
            organization=onboarding_link.organization,
            onboarding_link=onboarding_link,
            applicant_type=form.cleaned_data["applicant_type"],
            full_name=form.cleaned_data["full_name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            address=form.cleaned_data["address"],
            date_of_birth=form.cleaned_data["date_of_birth"],
            gender=form.cleaned_data["gender"],
            nin_masked=mask_identity_number(form.cleaned_data["nin"]),
            nin_hash=hash_sensitive_value(form.cleaned_data["nin"]),
            bvn_masked=mask_identity_number(form.cleaned_data["bvn"]),
            bvn_hash=hash_sensitive_value(form.cleaned_data["bvn"]),
            guarantor_name=form.cleaned_data["guarantor_name"],
            guarantor_phone=form.cleaned_data["guarantor_phone"],
            guarantor_relationship=form.cleaned_data["guarantor_relationship"],
        )
        ConsentRecord.objects.create(
            applicant=applicant,
            consent_text=consent_text,
            consent_version=consent_version,
            accepted=True,
            accepted_at=timezone.now(),
            ip_address=get_client_ip(request) or None,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        if form.cleaned_data.get("id_document"):
            f = form.cleaned_data["id_document"]
            document = ApplicantDocument.objects.create(
                applicant=applicant,
                document_type=form.cleaned_data["id_document_type"] or ApplicantDocument.DocumentTypes.ID_CARD,
                file=f,
                original_filename=f.name,
                mime_type=getattr(f, "content_type", ""),
                size=f.size,
            )
            log_event(
                onboarding_link.organization,
                None,
                "document.uploaded",
                "ApplicantDocument",
                str(document.id),
                {"document_type": document.document_type, "mime_type": document.mime_type, "size": document.size},
            )
        if form.cleaned_data.get("selfie"):
            f = form.cleaned_data["selfie"]
            document = ApplicantDocument.objects.create(
                applicant=applicant,
                document_type=ApplicantDocument.DocumentTypes.SELFIE,
                file=f,
                original_filename=f.name,
                mime_type=getattr(f, "content_type", ""),
                size=f.size,
            )
            log_event(
                onboarding_link.organization,
                None,
                "document.uploaded",
                "ApplicantDocument",
                str(document.id),
                {"document_type": document.document_type, "mime_type": document.mime_type, "size": document.size},
            )
        log_event(onboarding_link.organization, None, "applicant.submitted", "Applicant", str(applicant.id), {"source": "public_form"})
        return render(request, "applicants/submission_success.html", {"organization": onboarding_link.organization})
    return render(request, "applicants/onboarding_form.html", {"form": form, "organization": onboarding_link.organization, "onboarding_link": onboarding_link})

@login_required
def dashboard(request):
    ensure_dashboard_access(request.user)
    base_applicants = applicants_for_user(request.user)
    applicants = filter_applicants(base_applicants, request.GET)
    paginator = Paginator(applicants, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    documents = ApplicantDocument.objects.filter(applicant__in=base_applicants)
    verifications = VerificationRequest.objects.filter(applicant__in=base_applicants)
    status_counts = dict(base_applicants.values_list("status").annotate(total=Count("id")))
    summary = {
        "total": base_applicants.count(),
        "pending": status_counts.get(Applicant.Statuses.PENDING, 0),
        "under_review": status_counts.get(Applicant.Statuses.UNDER_REVIEW, 0),
        "approved": status_counts.get(Applicant.Statuses.APPROVED, 0),
        "rejected": status_counts.get(Applicant.Statuses.REJECTED, 0),
        "documents_pending": documents.filter(review_status=ApplicantDocument.ReviewStatuses.PENDING).count(),
        "verification_passed": verifications.filter(status=VerificationRequest.Statuses.VERIFIED).count(),
        "verification_failed": verifications.filter(status__in=[VerificationRequest.Statuses.FAILED, VerificationRequest.Statuses.ERROR]).count(),
    }
    return render(request, "dashboard/dashboard.html", {
        "applicants": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "onboarding_links": onboarding_links_for_user(request.user),
        "summary": summary,
        "filters": dashboard_filter_context(request.GET),
        "status_choices": Applicant.Statuses.choices,
        "applicant_type_choices": Applicant.ApplicantTypes.choices,
        "verification_status_choices": VerificationRequest.Statuses.choices,
        "document_review_status_choices": ApplicantDocument.ReviewStatuses.choices,
    })

@login_required
def applicant_detail(request, applicant_id):
    ensure_dashboard_access(request.user)
    applicant = get_object_or_404(applicants_for_user(request.user), id=applicant_id)
    form = ReviewForm(initial={"status": applicant.status})
    entity_ids = [str(applicant.id)]
    entity_ids.extend(str(document.id) for document in applicant.documents.all())
    entity_ids.extend(str(verification.id) for verification in applicant.verification_requests.all())
    audit_logs = applicant.organization.audit_logs.filter(entity_id__in=entity_ids)[:20]
    return render(request, "dashboard/applicant_detail.html", {"applicant": applicant, "form": form, "audit_logs": audit_logs})

@login_required
def review_applicant(request, applicant_id):
    ensure_dashboard_access(request.user)
    applicant = get_object_or_404(applicants_for_user(request.user), id=applicant_id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        applicant.status = form.cleaned_data["status"]
        applicant.save(update_fields=["status", "updated_at"])
        Review.objects.create(applicant=applicant, reviewer=request.user, status=form.cleaned_data["status"], note=form.cleaned_data["note"])
        log_event(applicant.organization, request.user, "applicant.reviewed", "Applicant", str(applicant.id), {"status": applicant.status})
        messages.success(request, "Applicant review updated.")
    else:
        messages.error(request, "Could not update review.")
    return redirect("applicant_detail", applicant_id=applicant.id)

@login_required
def export_applicants_csv(request):
    ensure_dashboard_access(request.user)
    applicants = filter_applicants(applicants_for_user(request.user), request.GET)
    return build_csv_response(applicants, request.user.organization, request.user)


@login_required
def bulk_applicant_action(request):
    ensure_dashboard_access(request.user)
    if request.method != "POST":
        return redirect("dashboard")

    action = request.POST.get("bulk_action", "")
    selected_ids = request.POST.getlist("selected_applicants")
    selected = applicants_for_user(request.user).filter(id__in=selected_ids).order_by("-submitted_at")
    selected_count = selected.count()
    if not selected_count:
        messages.error(request, "Select at least one applicant.")
        return redirect("dashboard")

    if action == "export_selected":
        return build_csv_response(
            selected,
            request.user.organization,
            request.user,
            action="applicant.bulk_exported",
            selected_count=selected_count,
        )

    status = BULK_ACTION_STATUS_MAP.get(action)
    if not status:
        messages.error(request, "Choose a valid bulk action.")
        return redirect("dashboard")

    updated_at = timezone.now()
    selected.update(status=status, updated_at=updated_at)
    for applicant in selected:
        Review.objects.create(applicant=applicant, reviewer=request.user, status=status, note="Bulk dashboard action.")
        log_event(
            applicant.organization,
            request.user,
            "applicant.bulk_reviewed",
            "Applicant",
            str(applicant.id),
            {"status": status, "bulk_action": action},
        )
    messages.success(request, f"{selected_count} applicant(s) updated.")
    return redirect("dashboard")
