from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from applicants import views as applicant_views
from reports import views as report_views
from verification import views as verification_views

urlpatterns = [
    path("", TemplateView.as_view(template_name="public/home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("dashboard/", applicant_views.dashboard, name="dashboard"),
    path("dashboard/applicants/<uuid:applicant_id>/", applicant_views.applicant_detail, name="applicant_detail"),
    path("dashboard/applicants/<uuid:applicant_id>/review/", applicant_views.review_applicant, name="review_applicant"),
    path("dashboard/applicants/<uuid:applicant_id>/export-report/", report_views.applicant_report_pdf, name="applicant_report_pdf"),
    path("dashboard/applicants/<uuid:applicant_id>/verify/", verification_views.run_mock_verification, name="run_mock_verification"),
    path("dashboard/export/applicants.csv", applicant_views.export_applicants_csv, name="export_applicants_csv"),
    path("onboard/<slug:organization_slug>/<uuid:token>/", applicant_views.onboarding_form, name="onboarding_form"),
    path("api/v1/", include("applicants.api_urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
