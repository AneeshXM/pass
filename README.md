# Self-Hosted Password Manager

A production-ready, self-hosted password manager for internal organizational use. Provides secure storage, management, and sharing of credentials.

## Features

- **User Management**: Registration, login, password reset, role-based access control (Admin, Manager, User)
- **Password Vault**: Store credentials with AES-256 encryption, search, filter, copy functionality
- **Team Collaboration**: Shared vaults, user groups, ownership, read-only/read-write permissions
- **Dashboard**: Statistics, recent activity, security alerts, expiring passwords
- **Audit Logging**: Track all user actions (logins, credential changes, sharing)
- **Backup & Restore**: Database backup, encrypted export files
- **Multi-Factor Authentication**: TOTP support with recovery codes

## Technology Stack

### Backend
- Python 3.11+ with FastAPI
- SQLAlchemy ORM
- PostgreSQL
- JWT Authentication with refresh tokens
- AES-256 Encryption for passwords
- bcrypt Password Hashing

### Frontend
- React 18+ with TypeScript
- Tailwind CSS
- React Router v6
- Axios for API calls

### Infrastructure
- Docker & Docker Compose
- Nginx Reverse Proxy
- Gunicorn ASGI server

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd password-manager
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

4. Access the application at `http://localhost` (or configured domain)

### Default Admin Credentials
- Email: admin@passwordmanager.local
- Password: ChangeMe123!

## Project Structure

```
password-manager/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API route handlers
│   │   ├── core/                 # Configuration, security
│   │   ├── models/               # Database models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   └── repositories/          # Data access layer
│   ├── migrations/               # Alembic migrations
│   └── tests/                    # Unit tests
├── frontend/
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Page components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API services
│   │   ├── context/              # React context providers
│   │   └── types/                # TypeScript types
│   └── public/                   # Static assets
├── nginx/                        # Nginx configuration
├── docs/                         # Documentation
└── docker-compose.yml            # Docker orchestration
```

## Security Features

- AES-256 encryption for stored passwords
- bcrypt password hashing (12 rounds)
- JWT authentication with access/refresh tokens
- Session timeout (configurable)
- Brute-force protection (rate limiting)
- CSRF protection
- XSS protection (React default)
- SQL injection protection (SQLAlchemy ORM)
- OWASP security best practices

## API Documentation

Once the server is running, access Swagger UI at:
- `http://localhost/api/v1/docs`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql://user:pass@db:5432/vault |
| `SECRET_KEY` | JWT secret key | (generate new) |
| `ENCRYPTION_KEY` | AES encryption key (32 bytes) | (generate new) |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | 7 |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | 60 |

## Backup & Restore

### Database Backup
```bash
docker-compose exec backend python -m app.core.backup --create
```

### Export Vault
```bash
docker-compose exec backend python -m app.core.backup --export
```

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## License

Internal use only.