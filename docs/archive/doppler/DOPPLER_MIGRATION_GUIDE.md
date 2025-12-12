# Secrets Management Migration Guide

## Overview

This guide covers the migration from `.env` files to **Doppler** secrets manager for Security Workstation.

**Why Doppler?**
- ✅ Free tier (5 users, unlimited secrets)
- ✅ Simple integration
- ✅ Automatic sync
- ✅ Audit logs
- ✅ CLI + Python SDK
- ✅ CI/CD integration

---

## Step 1: Install Doppler CLI

### Windows (PowerShell - Run as Administrator)

```powershell
iwr "https://cli.doppler.com/install.ps1" -useb | iex
```

### Linux/macOS

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | sudo apt-key add -
echo "deb https://packages.doppler.com/public/cli/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/doppler-cli.list
sudo apt-get update && sudo apt-get install doppler

# macOS
brew install dopplerhq/cli/doppler
```

### Verify Installation

```bash
doppler --version
# Expected: doppler version 3.x.x
```

---

## Step 2: Create Doppler Account & Login

```bash
# 1. Login (opens browser)
doppler login

# 2. Verify authentication
doppler me
```

---

## Step 3: Setup Project

```bash
# Navigate to project root
cd C:\Workstation

# Create project
doppler projects create security-workstation

# Create environments
doppler environments create dev --project security-workstation
doppler environments create staging --project security-workstation
doppler environments create production --project security-workstation

# Setup current directory
doppler setup --project security-workstation --config dev
```

---

## Step 4: Import Secrets from .env

### Option A: Automatic Import (Recommended)

```bash
# Import all secrets from .env file
doppler secrets upload .env --project security-workstation --config dev

# Verify import
doppler secrets
```

### Option B: Manual Import

```bash
# Backend secrets
doppler secrets set DATABASE_URL="postgresql://postgres:postgres@localhost:5432/security_workstation"

# AI API Keys
doppler secrets set OPENAI_API_KEY="your-key-here"
doppler secrets set ANTHROPIC_API_KEY="your-key-here"
doppler secrets set GEMINI_API_KEY="your-key-here"
doppler secrets set GIGACHAT_API_KEY="your-key-here"
doppler secrets set OPENROUTER_API_KEY="your-key-here"
doppler secrets set PERPLEXITY_API_KEY="your-key-here"

# Git tokens
doppler secrets set GITHUB_TOKEN="your-token-here"
doppler secrets set GITLAB_TOKEN="your-token-here"
doppler secrets set GITLAB_PROJECT_TOKEN="your-token-here"

# Other services
doppler secrets set TELEGRAM_BOT_TOKEN="your-token-here"
doppler secrets set SENTRY_DSN="your-dsn-here"

# Security settings
doppler secrets set ALLOWED_HOSTS="localhost,127.0.0.1"
doppler secrets set ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"
```

---

## Step 5: Update Application Code

### Backend Configuration

Create new config file with Doppler support:

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    When using Doppler: doppler run -- uvicorn app.main:app
    When using .env: uvicorn app.main:app (fallback)
    """
    
    # Database
    database_url: str
    
    # AI API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    gigachat_api_key: str | None = None
    openrouter_api_key: str | None = None
    perplexity_api_key: str | None = None
    
    # Git Tokens
    github_token: str | None = None
    gitlab_token: str | None = None
    gitlab_project_token: str | None = None
    
    # Other Services
    telegram_bot_token: str | None = None
    sentry_dsn: str | None = None
    
    # Security
    allowed_hosts: str = "localhost,127.0.0.1"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Rate Limiting
    redis_url: str | None = None
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"  # Fallback for local development without Doppler
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Global settings instance
settings = get_settings()
```

### Update main.py to use new config

```python
# backend/app/main.py
from app.config import settings

# Use settings instead of os.getenv
allowed_origins = settings.allowed_origins.split(",")
allowed_hosts = settings.allowed_hosts.split(",")
```

---

## Step 6: Update Docker Configuration

### Dockerfile (Production)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install Doppler CLI
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && apt-get install -y doppler && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with Doppler
CMD ["doppler", "run", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.dev (Development)

```dockerfile
# backend/Dockerfile.dev
FROM python:3.11-slim

# Install Doppler CLI
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && apt-get install -y doppler && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with Doppler and hot reload
CMD ["doppler", "run", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### podman-compose.yml

```yaml
# backend/podman-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: security-workstation-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: security_workstation
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: security-workstation-api
    environment:
      # Doppler token for service authentication
      - DOPPLER_TOKEN=${DOPPLER_TOKEN}
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app  # Hot reload
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  postgres_data:
```

---

## Step 7: Generate Service Tokens

### For Production Deployment

```bash
# Generate service token for production
doppler configs tokens create production-api --project security-workstation --config production

# Save the token (it will only be shown once!)
# Example: dp.st.production.xxxxxxxxxxxxxxxxxxxx
```

### For CI/CD

```bash
# Generate service token for CI/CD
doppler configs tokens create github-actions --project security-workstation --config production

# Add to GitHub Secrets:
# Settings → Secrets → Actions → New repository secret
# Name: DOPPLER_TOKEN
# Value: dp.st.production.xxxxxxxxxxxxxxxxxxxx
```

---

## Step 8: Update Development Workflow

### Local Development (Without Docker)

```bash
# Option 1: Run with Doppler
doppler run -- uvicorn app.main:app --reload

# Option 2: Run with Doppler (Python script)
doppler run -- python scripts/run_dev.py

# Option 3: Export to .env (for tools that don't support Doppler)
doppler secrets download --no-file --format env > .env.local
```

### Local Development (With Docker)

```bash
# 1. Generate local service token
doppler configs tokens create local-dev --project security-workstation --config dev

# 2. Save to .env.doppler (gitignored)
echo "DOPPLER_TOKEN=dp.st.dev.xxxxxxxxxxxxxxxxxxxx" > .env.doppler

# 3. Run with podman-compose
podman-compose --env-file .env.doppler up -d

# Or export token
export DOPPLER_TOKEN=dp.st.dev.xxxxxxxxxxxxxxxxxxxx
podman-compose up -d
```

---

## Step 9: Update .gitignore

```bash
# Add to .gitignore
echo "" >> .gitignore
echo "# Doppler" >> .gitignore
echo ".env.doppler" >> .gitignore
echo ".env.local" >> .gitignore
```

---

## Step 10: CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Doppler CLI
        uses: dopplerhq/cli-action@v3
      
      - name: Build and Deploy
        env:
          DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}
        run: |
          # Doppler automatically injects secrets
          doppler run -- docker build -t security-workstation-api .
          doppler run -- ./deploy.sh
```

### GitLab CI

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  image: docker:latest
  before_script:
    - apk add --no-cache curl
    - curl -Ls https://cli.doppler.com/install.sh | sh
  script:
    - doppler run -- docker build -t security-workstation-api .
    - doppler run -- ./deploy.sh
  variables:
    DOPPLER_TOKEN: $DOPPLER_TOKEN  # Set in GitLab CI/CD variables
  only:
    - main
```

---

## Step 11: Migrate Environments

### Development Environment

```bash
# Already done in Step 3
doppler setup --project security-workstation --config dev
doppler secrets upload .env
```

### Staging Environment

```bash
# Switch to staging
doppler setup --project security-workstation --config staging

# Copy from dev (or upload staging .env)
doppler secrets download --config dev --format env | doppler secrets upload --config staging

# Override staging-specific values
doppler secrets set DATABASE_URL="postgresql://user:pass@staging-db:5432/db" --config staging
doppler secrets set ALLOWED_ORIGINS="https://staging.securityworkstation.ai" --config staging
```

### Production Environment

```bash
# Switch to production
doppler setup --project security-workstation --config production

# Set production secrets (NEVER copy from dev!)
doppler secrets set DATABASE_URL="postgresql://user:pass@prod-db:5432/db" --config production
doppler secrets set ALLOWED_ORIGINS="https://securityworkstation.ai" --config production
doppler secrets set OPENAI_API_KEY="sk-prod-..." --config production
# ... set all production secrets
```

---

## Step 12: Security Best Practices

### 1. Rotate All Secrets

```bash
# After migration, rotate all API keys and tokens
# This ensures old .env secrets are invalidated

# Example: Rotate OpenAI key
# 1. Generate new key at https://platform.openai.com/api-keys
# 2. Update in Doppler
doppler secrets set OPENAI_API_KEY="sk-new-key" --config production
# 3. Delete old key from OpenAI dashboard
```

### 2. Enable Audit Logs

```bash
# View who accessed secrets
doppler activity

# View secret changes
doppler activity --config production
```

### 3. Set Up Alerts (Doppler Dashboard)

- Go to https://dashboard.doppler.com
- Project Settings → Integrations
- Add Slack/Email notifications for:
  - Secret changes
  - Token creation
  - Unauthorized access attempts

### 4. Principle of Least Privilege

```bash
# Create read-only tokens for monitoring
doppler configs tokens create monitoring --project security-workstation --config production --max-uses 1000

# Create limited-scope tokens for specific services
doppler configs tokens create backend-only --project security-workstation --config production
```

---

## Step 13: Backup & Recovery

### Backup Secrets

```bash
# Export all secrets to encrypted file
doppler secrets download --format env > secrets-backup-$(date +%Y%m%d).env.gpg

# Encrypt with GPG
gpg -c secrets-backup-$(date +%Y%m%d).env

# Store encrypted file in secure location (NOT in git!)
```

### Recovery

```bash
# Decrypt backup
gpg secrets-backup-20250104.env.gpg

# Restore to Doppler
doppler secrets upload secrets-backup-20250104.env --config production
```

---

## Step 14: Testing

### Test Local Development

```bash
# 1. Run with Doppler
cd backend
doppler run -- uvicorn app.main:app --reload

# 2. Test API
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# 3. Verify secrets are loaded
doppler run -- python -c "from app.config import settings; print(settings.database_url)"
```

### Test Docker

```bash
# 1. Build image
cd backend
podman build -t security-workstation-api:doppler -f Dockerfile .

# 2. Run with Doppler token
export DOPPLER_TOKEN=dp.st.dev.xxxxxxxxxxxxxxxxxxxx
podman run -d --name api-test \
  -p 8000:8000 \
  -e DOPPLER_TOKEN=$DOPPLER_TOKEN \
  security-workstation-api:doppler

# 3. Test
curl http://localhost:8000/health

# 4. Cleanup
podman stop api-test && podman rm api-test
```

---

## Step 15: Documentation

### Update README.md

Add Doppler setup instructions to backend/README.md:

```markdown
## 🔐 Secrets Management

This project uses **Doppler** for secrets management.

### Setup

1. Install Doppler CLI:
   ```bash
   # Windows
   iwr "https://cli.doppler.com/install.ps1" -useb | iex
   
   # Linux/macOS
   brew install dopplerhq/cli/doppler
   ```

2. Login:
   ```bash
   doppler login
   ```

3. Setup project:
   ```bash
   cd backend
   doppler setup --project security-workstation --config dev
   ```

4. Run application:
   ```bash
   doppler run -- uvicorn app.main:app --reload
   ```

### Without Doppler (Fallback)

Create `.env` file from `.env.example` and run normally:
```bash
uvicorn app.main:app --reload
```
```

---

## Troubleshooting

### Issue: "doppler: command not found"

```bash
# Verify installation
which doppler

# Reinstall
# Windows: Re-run PowerShell install script
# Linux: sudo apt-get install --reinstall doppler
```

### Issue: "Invalid token"

```bash
# Re-authenticate
doppler logout
doppler login

# Verify
doppler me
```

### Issue: "Secrets not loading in Docker"

```bash
# Check if DOPPLER_TOKEN is set
podman exec -it container-name env | grep DOPPLER_TOKEN

# Check Doppler CLI in container
podman exec -it container-name doppler me
```

### Issue: "Rate limit exceeded"

```bash
# Doppler free tier limits:
# - 100 requests/minute per token
# - Use service tokens for production (higher limits)
```

---

## Migration Checklist

- [ ] Install Doppler CLI
- [ ] Create Doppler account
- [ ] Create project and environments
- [ ] Import secrets from .env
- [ ] Update application code (config.py)
- [ ] Update Dockerfiles
- [ ] Update podman-compose.yml
- [ ] Generate service tokens
- [ ] Test local development
- [ ] Test Docker deployment
- [ ] Update CI/CD pipelines
- [ ] Rotate all secrets
- [ ] Enable audit logs
- [ ] Backup secrets
- [ ] Update documentation
- [ ] Delete old .env files (optional)

---

## Cost Estimate

### Doppler Free Tier (Current)
- ✅ 5 users
- ✅ Unlimited secrets
- ✅ 1 project
- ✅ 7-day audit logs
- **Cost: $0/month**

### If You Outgrow Free Tier

**Team Plan: $12/user/month**
- Unlimited projects
- 90-day audit logs
- Advanced integrations
- Priority support

**For 3 users: $36/month**

---

## Next Steps

1. **Complete migration** (this guide)
2. **Test thoroughly** in dev environment
3. **Deploy to staging** with Doppler
4. **Monitor for 1 week**
5. **Deploy to production**
6. **Rotate all production secrets**
7. **Delete old .env files** (keep .env.example)

---

## Support

- **Doppler Docs:** https://docs.doppler.com
- **Doppler Community:** https://community.doppler.com
- **Security Workstation Docs:** [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md)
