# AGENTS.md

## Project

VerifyFlow NG is a Nigerian digital identity onboarding and compliance automation platform.

The MVP helps businesses onboard customers, tenants, employees, students, cooperative members, agents, vendors, and applicants by collecting identity data, consent, uploaded documents, selfies, review notes, and PDF reports.

## Default Stack

- Backend: Django + Django REST Framework
- Database: SQLite for local dev; PostgreSQL for production
- Frontend: Django templates first for MVP speed
- Reports: ReportLab
- Future automation: webhooks and n8n

## Security Rules

Never commit real NIN values, real BVN values, real identity records, identity documents, selfies, API keys, provider credentials, production database URLs, or secrets.

Use fake seeded data only.

## Data Privacy Rules

- Treat applicant records as sensitive.
- Keep consent timestamp and consent text version.
- Store file references, not public file URLs.
- Avoid logging full identity numbers.
- Mask identity numbers in admin tables.
- Use environment variables for configuration.

## Django Apps

- accounts
- organizations
- applicants
- documents
- verification
- reports
- audit

## Build Order

1. Backend skeleton
2. Organization and user model
3. Applicant model
4. Public onboarding form
5. Document/selfie upload
6. Admin dashboard
7. PDF report
8. Mock verification provider
9. Landing page
10. Deployment preparation
