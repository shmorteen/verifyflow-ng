# GitHub Setup Commands

Run from the repository root after copying these files into `verifyflow-ng`.

```bash
git add .
git commit -m "Implement VerifyFlow NG MVP scaffold"
git push origin main
```

## Create Issues

```bash
gh issue create --repo shmorteen/verifyflow-ng --title '[M3] Validate Django backend skeleton locally' --body 'Run migrations, seed demo data, run tests, and confirm the app starts.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M4] Review core identity data model before production' --body 'Review model fields, sensitive data masking, and storage strategy.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M5] Polish applicant onboarding form UI' --body 'Improve form design, validation messages, and mobile layout.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M6] Improve dashboard permissions' --body 'Ensure users only access applicants belonging to their organization.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M7] Improve PDF report branding' --body 'Add organization logo, better formatting, and report numbering.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M8] Research real KYC/NIN/BVN provider options' --body 'Identify approved provider options and integration requirements.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M9] Add demo request form and lead capture' --body 'Store demo requests and optionally email notification.'
gh issue create --repo shmorteen/verifyflow-ng --title '[M10] Prepare production hosting plan' --body 'Choose hosting, storage, backup, error monitoring, and security hardening plan.'
```
