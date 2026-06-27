from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from applicants.models import Applicant
from .services import build_applicant_report_pdf

@login_required
def applicant_report_pdf(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id)
    pdf_buffer = build_applicant_report_pdf(applicant)
    return FileResponse(pdf_buffer, as_attachment=True, filename=f"verifyflow-report-{applicant.id}.pdf")
