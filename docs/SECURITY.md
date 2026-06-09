# Security Documentation

## Encryption

### Password Encryption (AES-256)
- All passwords in the vault are encrypted using AES-256-CBC
- Encryption key is stored in environment variable `ENCRYPTION_KEY`
- Each credential has a unique IV (Initialization Vector)
- Passwords are decrypted only when explicitly requested by the user

### Key Derivation
- Master password is hashed using bcrypt with 12 rounds
- Encryption key should be 32 bytes (256 bits) for AES-256

## Authentication

### JWT Tokens
- Access tokens expire in 30 minutes (configurable)
- Refresh tokens expire in 7 days (configurable)
- Tokens include user ID, roles, and expiration timestamp
- Invalid/expired tokens return 401 Unauthorized

### Password Hashing
- Algorithm: bcrypt
- Rounds: 12 (configurable)
- Salt: Auto-generated per password

## Session Management

### Session Timeout
- Inactive sessions timeout after 60 minutes (configurable)
- Sessions are invalidated on logout
- Multiple sessions per user are supported

### Brute Force Protection
- Login rate limited to 5 attempts per minute per IP
- After 5 failed attempts, account locked for 15 minutes
- Failed login attempts are logged in audit trail

## API Security

### Rate Limiting
- 100 requests per minute per user
- 20 requests per minute for authentication endpoints

### Input Validation
- All inputs are validated using Pydantic schemas
- SQL injection prevention via parameterized queries
- XSS prevention via React auto-escaping

### CORS
- Configurable allowed origins
- Credentials support enabled

## HTTPS Configuration

### Nginx SSL
- Generate SSL certificates or use Let's Encrypt
- TLS 1.2+ only
- Strong cipher suites

### Headers
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

## Database Security

### Connection
- PostgreSQL with password authentication
- Connection string in environment variable
- No credentials in code

### Migrations
- Alembic for database migrations
- Version control for schema changes

## Backup Security

### Export Files
- Exported files are encrypted with user-provided password
- Archive format with integrity verification

### Storage
- Backups stored in dedicated volume
- Access restricted to admin users

## Audit Logging

All security-relevant events are logged:
- Login attempts (success/failure)
- Password changes
- Credential creation/modification/deletion
- Sharing actions
- Admin actions
- MFA changes

## OWASP Compliance

### A01: Broken Access Control
- Role-based access control
- Ownership validation
- API endpoint authorization

### A02: Cryptographic Failures
- AES-256 encryption
- Secure key storage
- No sensitive data in URLs

### A03: Injection
- SQLAlchemy ORM
- Input validation
- Parameterized queries

### A04: Insecure Design
- Threat modeling
- Secure defaults
- Principle of least privilege

### A05: Security Misconfiguration
- Hardened Docker images
- Minimal packages
- Security headers

### A06: Vulnerable Components
- Regular updates
- Dependency scanning
- Minimal dependencies

### A07: Auth Failures
- Secure password storage
- MFA support
- Session management

### A08: Data Integrity Failures
- Integrity verification
- Secure backup/restore
- Audit trail

### A09: Logging Failures
- Structured logging
- Security event logging
- Log protection

### A10: SSRF Protection
- URL validation
- Whitelist approach
- Network segmentation

## Incident Response

1. Identify and contain the breach
2. Preserve evidence
3. Notify affected users
4. Remediate vulnerabilities
5. Update security measures
6. Document and review

## Security Checklist

- [ ] Change default admin password
- [ ] Generate new SECRET_KEY
- [ ] Generate new ENCRYPTION_KEY
- [ ] Configure HTTPS
- [ ] Set up backup schedule
- [ ] Enable MFA for admin accounts
- [ ] Review audit logs regularly
- [ ] Update dependencies
- [ ] Enable rate limiting
- [ ] Configure CORS properly