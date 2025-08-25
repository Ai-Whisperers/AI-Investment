# Security Configuration & Best Practices

## 🚨 CRITICAL: Pre-Deployment Security Checklist

### 1. **Rotate ALL Secrets Immediately**
Before deploying to production, generate new values for:
- [ ] `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- [ ] `ADMIN_TOKEN` - Generate with: `openssl rand -hex 32`
- [ ] `SESSION_SECRET_KEY` - Generate with: `openssl rand -hex 32`
- [ ] Database password - Use strong, unique password
- [ ] API keys - Obtain new keys from providers

### 2. **Environment Variables Setup**
Configure these ONLY in Render.com dashboard, NEVER in code:
```bash
# Security Keys (MUST REGENERATE)
SECRET_KEY=<new-32-byte-hex>
ADMIN_TOKEN=<new-32-byte-hex>
SESSION_SECRET_KEY=<new-32-byte-hex>

# Database (Render provides)
DATABASE_URL=<render-provided>

# API Keys (from providers)
TWELVEDATA_API_KEY=<your-key>
MARKETAUX_API_KEY=<your-key>
REDDIT_CLIENT_ID=<your-id>
REDDIT_CLIENT_SECRET=<your-secret>
GOOGLE_CLIENT_ID=<your-id>
GOOGLE_CLIENT_SECRET=<your-secret>
```

## 🔒 Security Measures Implemented

### Authentication & Authorization
- ✅ JWT tokens with expiration
- ✅ Bcrypt password hashing
- ✅ OAuth state validation (CSRF protection)
- ✅ Constant-time token comparison (timing attack prevention)
- ✅ HTTP-only cookies for OAuth state
- ✅ Session timeout configuration

### API Security
- ✅ Rate limiting (100 requests/minute)
- ✅ CORS configuration with specific origins
- ✅ Security headers (XSS, CSRF, clickjacking protection)
- ✅ HTTPS enforcement in production
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention via SQLAlchemy ORM

### OAuth Security
- ✅ State parameter validation
- ✅ Timeout for external API calls
- ✅ Secure redirect URI validation
- ✅ Error handling for failed attempts

## ⚠️ Known Security Considerations

### Token Storage (Frontend)
**Current**: Tokens stored in localStorage (development convenience)
**Production Recommendation**: Implement httpOnly cookies
```typescript
// TODO: Replace localStorage with secure cookie storage
// apps/web/app/services/api/base.ts
```

### Admin Authentication
**Enhanced with**:
- Constant-time comparison
- Rate limiting via middleware
- Consider adding:
  - IP whitelist for admin endpoints
  - 2FA for admin access
  - Audit logging

### Database Security
- Connection pooling configured
- SSL required for production connections
- Credentials never logged
- Prepared statements via ORM

## 🛡️ Security Headers

Production headers automatically applied:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## 📊 Rate Limiting

Current configuration:
- 100 requests per minute per IP
- Health checks excluded
- Consider adjusting based on usage patterns

## 🔐 Dependency Security

- Dependabot enabled for automatic updates
- Regular security audits via GitHub
- Pin versions in production
- Use `pip-audit` for Python packages

## 🚫 Never Do This

1. **NEVER** commit `.env` files
2. **NEVER** log sensitive data (passwords, tokens, keys)
3. **NEVER** use string concatenation for SQL queries
4. **NEVER** disable HTTPS in production
5. **NEVER** expose stack traces to users
6. **NEVER** trust user input without validation
7. **NEVER** store passwords in plain text
8. **NEVER** use default/weak secrets

## 📝 Security Incident Response

If a security issue is discovered:
1. Immediately rotate affected credentials
2. Review access logs for suspicious activity
3. Patch the vulnerability
4. Document the incident
5. Notify affected users if required

## 🔍 Security Testing

Before each deployment:
```bash
# Check for exposed secrets
git secrets --scan

# Python dependency audit
pip-audit

# Check for common vulnerabilities
bandit -r apps/api/app

# Frontend dependency audit
cd apps/web && npm audit
```

## 📞 Security Contact

Report security issues to: [Create private security advisory on GitHub]

---

**Last Security Review**: 2025-01-25
**Next Review Due**: Before production deployment