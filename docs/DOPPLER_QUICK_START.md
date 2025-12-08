# Doppler Quick Start Guide

**5-minute setup for Security Workstation**

## Step 1: Install Doppler CLI (2 min)

### Windows (PowerShell as Administrator)

```powershell
iwr "https://cli.doppler.com/install.ps1" -useb | iex
```

### Verify

```bash
doppler --version
# Expected: doppler version 3.x.x
```

---

## Step 2: Login & Setup (1 min)

```bash
# Login (opens browser)
doppler login

# Navigate to project
cd C:\Workstation

# Create project
doppler projects create security-workstation

# Setup dev environment
doppler setup --project security-workstation --config dev
```

---

## Step 3: Import Secrets (1 min)

### Option A: Automatic (Recommended)

```bash
# Import all secrets from .env
doppler secrets upload .env
```

### Option B: Manual

```bash
doppler secrets set DATABASE_URL="postgresql://postgres:postgres@localhost:5432/security_workstation"
doppler secrets set OPENAI_API_KEY="your-key"
# ... etc
```

---

## Step 4: Run Application (1 min)

### Local Development (Without Docker)

```bash
cd backend

# Run with Doppler
doppler run -- uvicorn app.main:app --reload

# Or run Python scripts
doppler run -- python scripts/your_script.py
```

### With Docker

```bash
# Generate service token
doppler configs tokens create local-dev --project security-workstation --config dev

# Copy token (shown only once!)
# Example: dp.st.dev.xxxxxxxxxxxxxxxxxxxx

# Set environment variable
# Windows PowerShell:
$env:DOPPLER_TOKEN="dp.st.dev.xxxxxxxxxxxxxxxxxxxx"

# Windows CMD:
set DOPPLER_TOKEN=dp.st.dev.xxxxxxxxxxxxxxxxxxxx

# Linux/macOS:
export DOPPLER_TOKEN=dp.st.dev.xxxxxxxxxxxxxxxxxxxx

# Run with podman-compose
cd backend
podman-compose up -d
```

---

## Verify Setup

```bash
# Check secrets
doppler secrets

# Test API
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Check config endpoint
curl http://localhost:8000/config
# Should show app info
```

---

## Common Commands

```bash
# View all secrets
doppler secrets

# Set a secret
doppler secrets set KEY="value"

# Delete a secret
doppler secrets delete KEY

# Download secrets to .env (for tools that don't support Doppler)
doppler secrets download --no-file --format env > .env.local

# Switch environment
doppler setup --config production

# View activity logs
doppler activity
```

---

## Production Setup

```bash
# Create production environment
doppler environments create production --project security-workstation

# Switch to production
doppler setup --config production

# Set production secrets (NEVER copy from dev!)
doppler secrets set DATABASE_URL="postgresql://prod-user:prod-pass@prod-db:5432/db"
doppler secrets set ALLOWED_ORIGINS="https://securityworkstation.ai"
# ... set all production secrets

# Generate production service token
doppler configs tokens create production-api --project security-workstation --config production

# Save token to CI/CD secrets
# GitHub: Settings → Secrets → Actions → DOPPLER_TOKEN
# GitLab: Settings → CI/CD → Variables → DOPPLER_TOKEN
```

---

## Troubleshooting

### "doppler: command not found"

```bash
# Windows: Re-run PowerShell install script as Administrator
# Linux: sudo apt-get install --reinstall doppler
# macOS: brew reinstall dopplerhq/cli/doppler
```

### "Not authenticated"

```bash
doppler logout
doppler login
```

### "Invalid token" in Docker

```bash
# Check if token is set
echo $DOPPLER_TOKEN  # Linux/macOS
echo %DOPPLER_TOKEN%  # Windows CMD
echo $env:DOPPLER_TOKEN  # Windows PowerShell

# Regenerate token
doppler configs tokens create new-token --project security-workstation --config dev
```

---

## Migration Script

For automated migration from .env:

```bash
# Dry run (preview only)
python scripts/migrate_to_doppler.py \
  --env-file .env \
  --project security-workstation \
  --config dev \
  --dry-run

# Actual migration
python scripts/migrate_to_doppler.py \
  --env-file .env \
  --project security-workstation \
  --config dev
```

---

## Next Steps

1. ✅ Secrets migrated to Doppler
2. ✅ Application running with Doppler
3. 📝 **Rotate all API keys** (old .env keys are compromised)
4. 📝 Setup staging environment
5. 📝 Setup production environment
6. 📝 Configure CI/CD with Doppler tokens
7. 📝 Enable audit logs & alerts

---

## Full Documentation

- [Complete Migration Guide](DOPPLER_MIGRATION_GUIDE.md)
- [Security Improvements](SECURITY_IMPROVEMENTS.md)
- [Doppler Official Docs](https://docs.doppler.com)

---

**Questions?** Check [DOPPLER_MIGRATION_GUIDE.md](DOPPLER_MIGRATION_GUIDE.md) for detailed instructions.
