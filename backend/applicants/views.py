import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from audit.services import log_event
from documents.models import ApplicantDocument
from organizations.models import OnboardingLink
from .forms import ApplicantOnboardingForm, CONSENT_TEXT, ReviewForm
from .models import Applicant, ConsentRecord, ConsentTemplate, Review
from .utils import get_client_ip, hash_sensitive_value, mask_identity_number

def applicants_for_user(user):
    applicants = Applicant.objects.select_related("organization")
    if user.organization:
        applicants = applicants.filter(organization=user.organization)
    return applicants

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
            ApplicantDocument.objects.create(applicant=applicant, document_type=ApplicantDocument.DocumentTypes.ID_CARD, file=f, original_filename=f.name, mime_type=getattr(f, "content_type", ""), size=f.size)
        if form.cleaned_data.get("selfie"):
            f = form.cleaned_data["selfie"]
            ApplicantDocument.objects.create(applicant=applicant, document_type=ApplicantDocument.DocumentTypes.SELFIE, file=f, original_filename=f.name, mime_type=getattr(f, "content_type", ""), size=f.size)
        log_event(onboarding_link.organization, None, "applicant.submitted", "Applicant", str(applicant.id), {"source": "public_form"})
        return render(request, "applicants/submission_success.html", {"organization": onboarding_link.organization})
    return render(request, "applicants/onboarding_form.html", {"form": form, "organization": onboarding_link.organization, "onboarding_link": onboarding_link})

@login_required
def dashboard(request):
    applicants = applicants_for_user(request.user).order_by("-submitted_at")
    onboarding_links = OnboardingLink.objects.filter(is_active=True).select_related("organization").order_by("label")
    if request.user.organization:
        onboarding_links = onboarding_links.filter(organization=request.user.organization)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if query:
        applicants = applicants.filter(full_name__icontains=query)
    if status:
        applicants = applicants.filter(status=status)
    return render(request, "dashboard/dashboard.html", {
        "applicants": applicants,
        "onboarding_links": onboarding_links,
        "query": query,
        "status": status,
    })

@login_required
def applicant_detail(request, applicant_id):
    applicant = get_object_or_404(applicants_for_user(request.user), id=applicant_id)
    form = ReviewForm(initial={"status": applicant.status})
    return render(request, "dashboard/applicant_detail.html", {"applicant": applicant, "form": form})

@login_required
def review_applicant(request, applicant_id):
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
    applicants = applicants_for_user(request.user).order_by("-submitted_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="verifyflow_applicants.csv"'
    writer = csv.writer(response)
    writer.writerow(["Full name", "Phone", "Email", "Applicant type", "NIN", "BVN", "Status", "Submitted at"])
    for applicant in applicants:
        writer.writerow([applicant.full_name, applicant.phone, applicant.email, applicant.get_applicant_type_display(), applicant.nin_masked, applicant.bvn_masked, applicant.get_status_display(), applicant.submitted_at.isoformat()])
    return response
