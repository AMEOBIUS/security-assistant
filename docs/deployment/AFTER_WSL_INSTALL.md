# 🚀 After WSL Install - Podman Setup

## Step 1: Verify WSL

```powershell
wsl --version
# Should show: WSL version >= 1.2.5

wsl --list --verbose
# Should show: Ubuntu or default distro
```

---

## Step 2: Setup Podman Machine

```powershell
# Initialize Podman machine (uses WSL)
podman machine init

# Start machine
podman machine start

# Verify
podman --version
podman ps
```

---

## Step 3: Start Backend

```powershell
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

## Step 4: Test API

```powershell
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# API docs
start http://localhost:8000/docs

# Test waitlist
curl -X POST http://localhost:8000/api/waitlist `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"test@example.com\",\"name\":\"Test User\"}'
```

---

## 🐛 Troubleshooting

### "podman machine init" fails:
```powershell
# Use Podman Desktop GUI instead
# Open Podman Desktop → Settings → Resources → Create Machine
```

### "podman-compose: command not found":
```powershell
# Install podman-compose
pip install podman-compose

# Or use Podman Desktop GUI to import compose file
```

### Containers won't start:
```powershell
# Check machine is running
podman machine list

# Restart machine
podman machine stop
podman machine start

# Try again
podman-compose up -d
```

---

## ✅ Success Criteria

- [ ] `wsl --version` shows >= 1.2.5
- [ ] `podman --version` works
- [ ] `podman ps` shows containers
- [ ] http://localhost:8000/health returns healthy
- [ ] http://localhost:8000/docs shows Swagger UI

---

## 🚀 Continue Session 24

After backend works:
1. Deploy to production (Fly.io)
2. Connect landing page
3. Test email capture
4. Launch marketing

---

**See you after reboot!** 🎯
