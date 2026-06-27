from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api import ApplicantViewSet

router = DefaultRouter()
router.register("applicants", ApplicantViewSet, basename="applicant")

urlpatterns = [path("", include(router.urls))]
