import uuid
from django.db import models
from django.utils.text import slugify

class Organization(models.Model):
    class BusinessTypes(models.TextChoices):
        REAL_ESTATE = "real_estate", "Real Estate"
        COOPERATIVE = "cooperative", "Cooperative / Loans"
        HR = "hr", "HR / Recruitment"
        SCHOOL = "school", "School / Training"
        SME = "sme", "SME"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    business_type = models.CharField(max_length=40, choices=BusinessTypes.choices, default=BusinessTypes.SME)
    logo = models.ImageField(upload_to="organization_logos/", blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "organization"
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class OnboardingLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="onboarding_links")
    label = models.CharField(max_length=120, default="Default onboarding link")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    applicant_type_default = models.CharField(max_length=40, default="customer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def public_path(self):
        return f"/onboard/{self.organization.slug}/{self.token}/"

    def __str__(self):
        return f"{self.organization.name} — {self.label}"
