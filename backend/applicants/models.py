import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class Applicant(models.Model):
    class ApplicantTypes(models.TextChoices):
        TENANT = "tenant", "Tenant"
        EMPLOYEE = "employee", "Employee"
        STUDENT = "student", "Student"
        CUSTOMER = "customer", "Customer"
        MEMBER = "member", "Cooperative Member"
        AGENT = "agent", "Agent"
        VENDOR = "vendor", "Vendor"
        OTHER = "other", "Other"

    class Statuses(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other / Prefer not to say"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="applicants")
    onboarding_link = models.ForeignKey("organizations.OnboardingLink", on_delete=models.SET_NULL, null=True, blank=True, related_name="applicants")
    applicant_type = models.CharField(max_length=40, choices=ApplicantTypes.choices, default=ApplicantTypes.CUSTOMER)
    full_name = models.CharField(max_length=180)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    nin_masked = models.CharField(max_length=20, blank=True)
    nin_hash = models.CharField(max_length=128, blank=True)
    bvn_masked = models.CharField(max_length=20, blank=True)
    bvn_hash = models.CharField(max_length=128, blank=True)
    guarantor_name = models.CharField(max_length=180, blank=True)
    guarantor_phone = models.CharField(max_length=30, blank=True)
    guarantor_relationship = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=30, choices=Statuses.choices, default=Statuses.PENDING)
    submitted_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_identifier(self):
        return self.nin_masked or self.bvn_masked or "No masked ID"

    def __str__(self):
        return f"{self.full_name} — {self.organization.name}"

class ConsentRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name="consent")
    consent_text = models.TextField()
    consent_version = models.CharField(max_length=30, default="v1")
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"Consent for {self.applicant.full_name}"

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=Applicant.Statuses.choices)
    note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-reviewed_at"]

    def __str__(self):
        return f"{self.applicant.full_name} — {self.status}"
