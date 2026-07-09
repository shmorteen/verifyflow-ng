from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from applicants import views as applicant_views
from documents import views as document_views
from reports import views as report_views
from verification import views as verification_views

urlpatterns = [
    path("", TemplateView.as_view(template_name="public/home.html"), name="home"),
    path(
        "privacy/",
        TemplateView.as_view(template_name="legal/privacy_policy.html"),
        name="privacy_policy",
    ),
    path(
        "terms/",
        TemplateView.as_view(template_name="legal/terms_of_use.html"),
        name="terms_of_use",
    ),
    path(
        "data-retention/",
        TemplateView.as_view(template_name="legal/data_retention.html"),
        name="data_retention_policy",
    ),
    path(
        "data-subject-rights/",
        TemplateView.as_view(template_name="legal/data_subject_rights.html"),
        name="data_subject_rights",
    ),
    path("admin/", admin.site.urls),
    path("dashboard/", applicant_views.dashboard, name="dashboard"),
    path("dashboard/applicants/<uuid:applicant_id>/", applicant_views.applicant_detail, name="applicant_detail"),
    path("dashboard/applicants/<uuid:applicant_id>/review/", applicant_views.review_applicant, name="review_applicant"),
    path("dashboard/applicants/<uuid:applicant_id>/export-report/", report_views.applicant_report_pdf, name="applicant_report_pdf"),
    path("dashboard/applicants/<uuid:applicant_id>/verify/", verification_views.run_mock_verification, name="run_mock_verification"),
    path("dashboard/applicants/bulk/", applicant_views.bulk_applicant_action, name="bulk_applicant_action"),
    path("dashboard/documents/<uuid:document_id>/download/", document_views.download_document, name="download_document"),
    path("dashboard/documents/<uuid:document_id>/review/", document_views.review_document, name="review_document"),
    path("dashboard/export/applicants.csv", applicant_views.export_applicants_csv, name="export_applicants_csv"),
    path("onboard/<slug:organization_slug>/<uuid:token>/", applicant_views.onboarding_form, name="onboarding_form"),
    path("api/v1/", include("applicants.api_urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
