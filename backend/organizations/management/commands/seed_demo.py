from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from applicants.forms import CONSENT_TEXT
from applicants.models import ConsentTemplate
from organizations.models import OnboardingLink, Organization

class Command(BaseCommand):
    help = "Seed demo organization, admin user, and onboarding link."

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug="demo-property-managers",
            defaults={
                "name": "Demo Property Managers",
                "business_type": Organization.BusinessTypes.REAL_ESTATE,
                "contact_email": "hello@verifyflow.local",
                "contact_phone": "+2340000000000",
            },
        )
        link, _ = OnboardingLink.objects.get_or_create(
            organization=org,
            label="Tenant onboarding",
            defaults={"applicant_type_default": "tenant"},
        )
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="admin@verifyflow.local",
            defaults={
                "email": "admin@verifyflow.local",
                "organization": org,
                "role": "owner",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("ChangeMe123!")
            user.save()
        ConsentTemplate.objects.get_or_create(
            version="v1",
            defaults={
                "title": "Demo onboarding consent",
                "body": CONSENT_TEXT,
                "is_active": True,
            },
        )
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Admin username/email: admin@verifyflow.local")
        self.stdout.write("Admin password: ChangeMe123!")
        self.stdout.write(f"Onboarding URL: http://127.0.0.1:8000{link.public_path()}")
