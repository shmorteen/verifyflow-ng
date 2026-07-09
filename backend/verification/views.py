from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from applicants.views import applicants_for_user, ensure_dashboard_access
from audit.services import log_event
from .models import VerificationRequest
from .services import run_mock_verification_for_applicant

@login_required
def run_mock_verification(request, applicant_id):
    ensure_dashboard_access(request.user)
    applicant = get_object_or_404(applicants_for_user(request.user), id=applicant_id)
    verification_type = request.POST.get("verification_type", VerificationRequest.VerificationTypes.NIN)
    verification = run_mock_verification_for_applicant(applicant, verification_type)
    log_event(applicant.organization, request.user, "verification.mock_run", "VerificationRequest", str(verification.id), {"status": verification.status})
    messages.success(request, f"Mock {verification_type.upper()} verification completed: {verification.get_status_display()}.")
    return redirect("applicant_detail", applicant_id=applicant.id)
