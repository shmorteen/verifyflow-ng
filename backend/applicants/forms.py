from django import forms
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
    id_document = forms.FileField(required=False)
    selfie = forms.FileField(required=False)
    consent = forms.BooleanField(required=True, label=CONSENT_TEXT)

    def __init__(self, *args, consent_text=CONSENT_TEXT, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["consent"].label = consent_text

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("nin") and not cleaned.get("bvn"):
            raise forms.ValidationError("Provide at least a NIN or BVN for onboarding.")
        return cleaned

class ReviewForm(forms.Form):
    status = forms.ChoiceField(choices=Applicant.Statuses.choices)
    note = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)
