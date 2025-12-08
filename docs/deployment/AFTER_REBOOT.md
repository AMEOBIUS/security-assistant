# 🚀 After Reboot - Quick Start

## Step 1: Initialize Podman Machine

```powershell
# Create machine with Hyper-V
podman machine init --driver hyperv

# Start machine
podman machine start

# Verify
podman --version
podman ps
```

---

## Step 2: Test Backend

```powershell
# Navigate to backend
cd C:\Workstation\backend

# Start services
podman-compose up -d

# Check logs
podman-compose logs -f api

# Should see:
# "Application startup complete"
# "Uvicorn running on http://0.0.0.0:8000"
```

---

## Step 3: Test API

```powershell
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# API docs (open in browser)
start http://localhost:8000/docs

# Test waitlist endpoint
curl -X POST http://localhost:8000/api/waitlist `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","name":"Test User"}'
```

---

## 🐛 Troubleshooting

### Podman machine won't start:
```powershell
# Check Hyper-V is enabled
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V

# Should show: State = Enabled

# If not, run again:
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

### Port 8000 already in use:
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Database connection failed:
```powershell
# Check if DB container running
podman-compose ps

# Restart DB
podman-compose restart db

# Check DB logs
podman-compose logs db
```

---

## ✅ Success Criteria

- [ ] `podman ps` shows 2 containers (api, db)
- [ ] http://localhost:8000/health returns healthy
- [ ] http://localhost:8000/docs shows Swagger UI
- [ ] Can add email to waitlist via API

---

## 🚀 Next Steps

After backend works locally:
1. Deploy to Fly.io (easiest)
2. Connect landing page
3. Test email capture
4. Launch marketing

---

**See you after reboot!** 🎯

Save this file: `AFTER_REBOOT.md`
