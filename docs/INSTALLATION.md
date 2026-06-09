# Installation Guide

## Prerequisites

- Docker 20.10+ 
- Docker Compose 2.0+
- Git
- 4GB RAM minimum
- 20GB disk space

## Quick Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd password-manager
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` file with your settings:
```bash
# Required - Generate new keys!
SECRET_KEY=your-super-secret-key-change-this
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Database
DATABASE_URL=postgresql://vault_user:your_secure_password@db:5432/vault

# Domain
DOMAIN=localhost
```

### 3. Generate Secure Keys
```bash
# Generate SECRET_KEY (64 random characters)
openssl rand -hex 32

# Generate ENCRYPTION_KEY (32 bytes base64 encoded)
openssl rand -base64 32
```

### 4. Start Services
```bash
docker-compose up -d
```

### 5. Verify Installation
```bash
docker-compose ps
docker-compose logs backend
```

### 6. Access Application
- URL: http://localhost (or your configured domain)
- Admin email: admin@passwordmanager.local
- Admin password: ChangeMe123!

## Manual Installation (Without Docker)

### Backend Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE vault;
CREATE USER vault_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE vault TO vault_user;
```

2. Install Python dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL="postgresql://vault_user:pass@localhost:5432/vault"
export SECRET_KEY="your-secret-key"
export ENCRYPTION_KEY="your-encryption-key"
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install Node dependencies:
```bash
cd frontend
npm install
```

2. Build for production:
```bash
npm run build
```

3. Serve with Nginx (see nginx configuration)

## SSL/TLS Setup

### Self-Signed Certificate (Development)
```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Let's Encrypt (Production)
```bash
certbot --nginx -d yourdomain.com
```

Update `docker-compose.yml` to mount SSL certificates.

## Database Migrations

### Initial Setup
```bash
docker-compose exec backend alembic upgrade head
```

### Create Migration
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Rollback
```bash
docker-compose exec backend alembic downgrade -1
```

## Backup Configuration

### Automated Backups
Add to crontab:
```bash
0 2 * * * docker-compose exec backend python -m app.core.backup --create
```

### Backup Retention
Modify backup script to keep last 30 days of backups.

## Firewall Configuration

### UFW (Ubuntu)
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### iptables
```bash
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## Reverse Proxy (Nginx)

The included nginx configuration handles:
- SSL termination
- Static file serving
- API proxy to backend
- Security headers

## Troubleshooting

### Database Connection Issues
```bash
docker-compose exec db psql -U vault_user -d vault
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Clear Cache
```bash
docker-compose exec backend python -c "from app.core.cache import clear_cache; clear_cache()"
```

## Production Checklist

- [ ] Change default admin password
- [ ] Generate new SECRET_KEY
- [ ] Generate new ENCRYPTION_KEY
- [ ] Configure HTTPS/SSL
- [ ] Set up automated backups
- [ ] Configure firewall
- [ ] Enable MFA for all admin accounts
- [ ] Set up monitoring
- [ ] Review security settings
- [ ] Test backup/restore