# Deployment Checklist

## Environment

- [ ] Set strong `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Set production `ALLOWED_HOSTS`
- [ ] Configure PostgreSQL `DATABASE_URL`
- [ ] Configure static files
- [ ] Configure secure media storage
- [ ] Configure HTTPS

## Security

- [ ] Restrict dashboard access
- [ ] Add 2FA for staff accounts
- [ ] Add upload file size limits
- [ ] Add upload MIME validation
- [ ] Add virus scanning for files
- [ ] Avoid logging full identity values
- [ ] Mask identity values in dashboard

## Data Protection

- [ ] Confirm consent text
- [ ] Add privacy notice
- [ ] Define data retention policy
- [ ] Define deletion/export process
- [ ] Review with legal/privacy professional
