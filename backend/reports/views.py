from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from audit.services import log_event
from applicants.views import applicants_for_user, ensure_dashboard_access
from .services import applicant_report_filename, generate_applicant_report

@login_required
def applicant_report_pdf(request, applicant_id):
    ensure_dashboard_access(request.user)
    applicant = get_object_or_404(applicants_for_user(request.user), id=applicant_id)
    report_record, pdf_buffer = generate_applicant_report(applicant, request.user)
    log_event(
        applicant.organization,
        request.user,
        "report.downloaded",
        "ReportRecord",
        str(report_record.id),
        {
            "report_reference": report_record.report_reference,
            "applicant_id": str(applicant.id),
        },
    )
    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=applicant_report_filename(applicant, report_record.generated_at),
    )
