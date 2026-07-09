from django import forms
from django.conf import settings
from documents.models import ApplicantDocument
from documents.validators import ALLOWED_FILE_TYPES_TEXT, format_file_size, validate_uploaded_document
from .models import Applicant

CONSENT_TEXT = (
    "By submitting this form, I confirm that the information provided is accurate "
    "and I authorize the business to collect, store, review, and use my identity "
    "information and uploaded documents for onboarding, verification, compliance, "
    "and record-keeping purposes."
)

class ApplicantOnboardingForm(forms.Form):
    applicant_type = forms.ChoiceField(choices=Applicant.ApplicantTypes.choices)
    full_name = forms.CharField(max_length=180)
    phone = forms.CharField(max_length=30)
    email = forms.EmailField(required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(choices=[("", "Select gender")] + list(Applicant.Gender.choices), required=False)
    nin = forms.CharField(max_length=11, required=False, help_text="11-digit NIN. Stored as masked/hash value in MVP.")
    bvn = forms.CharField(max_length=11, required=False, help_text="Optional 11-digit BVN. Stored as masked/hash value in MVP.")
    guarantor_name = forms.CharField(max_length=180, required=False)
    guarantor_phone = forms.CharField(max_length=30, required=False)
    guarantor_relationship = forms.CharField(max_length=80, required=False)
    id_document_type = forms.ChoiceField(
        choices=[
            (ApplicantDocument.DocumentTypes.ID_CARD, "ID Card"),
            (ApplicantDocument.DocumentTypes.NIN_SLIP, "NIN Slip"),
            (ApplicantDocument.DocumentTypes.PASSPORT, "Passport"),
            (ApplicantDocument.DocumentTypes.UTILITY_BILL, "Utility Bill"),
            (ApplicantDocument.DocumentTypes.OTHER, "Other"),
        ],
        required=False,
        label="Identity document category",
    )
    id_document = forms.FileField(required=False, label="Identity document")
    selfie = forms.FileField(required=False, label="Selfie")
    consent = forms.BooleanField(required=True, label=CONSENT_TEXT)

    def __init__(self, *args, consent_text=CONSENT_TEXT, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["consent"].label = consent_text
        upload_help = (
            f"Accepted file types: {ALLOWED_FILE_TYPES_TEXT}. "
            f"Maximum size: {format_file_size(settings.MAX_UPLOAD_SIZE_BYTES)}."
        )
        self.fields["id_document"].help_text = upload_help
        self.fields["selfie"].help_text = upload_help

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("nin") and not cleaned.get("bvn"):
            raise forms.ValidationError("Provide at least a NIN or BVN for onboarding.")
        if cleaned.get("id_document") and not cleaned.get("id_document_type"):
            self.add_error("id_document_type", "Choose the document category for the uploaded identity document.")
        return cleaned

    def clean_id_document(self):
        return validate_uploaded_document(self.cleaned_data.get("id_document"))

    def clean_selfie(self):
        return validate_uploaded_document(self.cleaned_data.get("selfie"))

class ReviewForm(forms.Form):
    status = forms.ChoiceField(choices=Applicant.Statuses.choices)
    note = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)
