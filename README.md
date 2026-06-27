# VerifyFlow NG

VerifyFlow NG is a digital identity onboarding and compliance automation platform for Nigerian businesses.

## MVP Status

This codebase contains an implementable Django MVP scaffold covering:

- M1 — Product Foundation
- M2 — Repo and Codex Setup
- M3 — Backend Skeleton
- M4 — Data Model
- M5 — Applicant Onboarding Form
- M6 — Admin Dashboard
- M7 — Report Generation
- M8 — Verification Provider Layer
- M9 — Landing Page and Ads Readiness
- M10 — Deployment Preparation

## Target Users

- Real estate agents and property managers
- Cooperatives and loan businesses
- HR and recruitment teams
- Schools and training centers
- SMEs onboarding agents, vendors, or field workers

## MVP Promise

> Send a secure onboarding link, collect identity documents and consent, review the submission, and generate a verification report.

## Stack

- Django + Django REST Framework
- SQLite locally; PostgreSQL-ready for production
- Django templates for MVP UI
- ReportLab PDF reports
- Docker/Docker Compose scaffold
- GitHub Actions CI scaffold

## Local Setup

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Demo admin:

```text
Username: admin@verifyflow.local
Password: ChangeMe123!
```

Important: do not commit real NINs, BVNs, customer data, identity documents, selfies, API keys, access tokens, or provider credentials.
