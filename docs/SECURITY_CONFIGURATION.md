# Security Configuration Guide

## 🔐 Critical Security Notice

**NEVER commit credentials, API keys, or secrets to version control!**

## Environment Variables Management

### Local Development
1. Copy `.env.example` to `.env` in the appropriate directory
2. Fill in your local development values
3. Never commit the `.env` file to git

### Production Deployment (Render.com)
1. Go to your service dashboard on Render.com
2. Navigate to "Environment" tab
3. Add each environment variable with production values
4. Use Render's secret management for sensitive values

## Required Credentials

### Backend (apps/api/)
- `SECRET_KEY`: JWT signing key (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `DATABASE_URL`: PostgreSQL connection string
- `ADMIN_TOKEN`: Admin API authentication token
- `TWELVEDATA_API_KEY`: Market data API key (get from https://twelvedata.com)

### Frontend (apps/web/)
- `NEXT_PUBLIC_API_URL`: Backend API URL (public, safe to commit)

## Security Best Practices

### 1. Credential Rotation
- Rotate all credentials every 90 days
- Immediately rotate if exposed or compromised
- Use different credentials for each environment

### 2. Secret Generation
```bash
# Generate secure random secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using openssl
openssl rand -base64 32
```

### 3. Git Security
```bash
# Ensure .env files are never tracked
git rm --cached .env
git rm --cached apps/api/.env
git rm --cached apps/web/.env

# Verify .gitignore includes
echo "*.env" >> .gitignore
echo ".env.*" >> .gitignore
```

### 4. Database Security
- Use SSL connections in production
- Implement connection pooling
- Use read-only credentials where possible
- Regular backups with encryption

### 5. API Key Management
- Use different API keys for development and production
- Implement rate limiting
- Monitor API usage
- Use API key rotation policies

## Emergency Response

### If Credentials Are Exposed:
1. **Immediately** rotate all affected credentials
2. Update credentials in production environment
3. Check logs for unauthorized access
4. Notify team and users if data was compromised
5. Document incident and prevention measures

## Compliance Checklist

- [ ] All `.env` files in `.gitignore`
- [ ] No hardcoded secrets in code
- [ ] Production credentials in environment variables only
- [ ] Regular credential rotation schedule
- [ ] Monitoring for exposed secrets (GitHub scanning)
- [ ] Encrypted database connections
- [ ] HTTPS enforced for all endpoints
- [ ] Rate limiting implemented
- [ ] Admin endpoints properly authenticated

## Tools for Secret Scanning

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Add secret scanning
pre-commit install
```

### GitHub Secret Scanning
- Enable in repository settings
- Review alerts regularly
- Act on exposed secrets immediately

## Contact

For security concerns or to report vulnerabilities:
- Create a private security advisory on GitHub
- Do NOT create public issues for security vulnerabilities