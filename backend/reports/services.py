from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

def build_applicant_report_pdf(applicant):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - inch
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(inch, y, "VerifyFlow NG Applicant Report")
    y -= 0.4 * inch
    pdf.setFont("Helvetica", 10)
    rows = [
        ("Organization", applicant.organization.name),
        ("Full name", applicant.full_name),
        ("Phone", applicant.phone),
        ("Email", applicant.email or "N/A"),
        ("Applicant type", applicant.get_applicant_type_display()),
        ("Address", applicant.address or "N/A"),
        ("NIN", applicant.nin_masked or "N/A"),
        ("BVN", applicant.bvn_masked or "N/A"),
        ("Status", applicant.get_status_display()),
        ("Submitted at", applicant.submitted_at.strftime("%Y-%m-%d %H:%M")),
    ]
    for label, value in rows:
        pdf.drawString(inch, y, f"{label}:")
        pdf.drawString(2.3 * inch, y, str(value)[:85])
        y -= 0.23 * inch
    y -= 0.2 * inch
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(inch, y, "Consent Summary")
    y -= 0.3 * inch
    pdf.setFont("Helvetica", 10)
    consent = getattr(applicant, "consent", None)
    if consent:
        pdf.drawString(inch, y, f"Accepted: {consent.accepted}")
        y -= 0.23 * inch
        pdf.drawString(inch, y, f"Accepted at: {consent.accepted_at.strftime('%Y-%m-%d %H:%M') if consent.accepted_at else 'N/A'}")
        y -= 0.23 * inch
        pdf.drawString(inch, y, f"Consent version: {consent.consent_version}")
    else:
        pdf.drawString(inch, y, "No consent record found.")
    y -= 0.45 * inch
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(inch, y, "Latest Review")
    y -= 0.3 * inch
    pdf.setFont("Helvetica", 10)
    latest_review = applicant.reviews.first()
    if latest_review:
        pdf.drawString(inch, y, f"Reviewer: {latest_review.reviewer or 'N/A'}")
        y -= 0.23 * inch
        pdf.drawString(inch, y, f"Status: {latest_review.get_status_display()}")
        y -= 0.23 * inch
        pdf.drawString(inch, y, f"Note: {(latest_review.note or 'N/A')[:90]}")
    else:
        pdf.drawString(inch, y, "No review recorded yet.")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
