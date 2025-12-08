# 🧪 Test Landing Page with Backend

## Setup

### Terminal 1: Backend API
```powershell
cd C:\Workstation\backend
$env:DATABASE_URL="sqlite:///./waitlist.db"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend
```powershell
cd C:\Workstation\frontend\landing
python -m http.server 8001
```

### Terminal 3: Test
```powershell
# Open landing page
start http://localhost:8001

# Fill form with NEW email
# Click "Get Early Access"
# Should see success message!

# Check backend received it:
curl http://localhost:8000/api/waitlist/count
```

---

## ✅ Success Criteria

- [ ] Form submits without errors
- [ ] Success message appears
- [ ] Backend shows increased count
- [ ] No CORS errors in browser console

---

## 🚀 Next: Deploy to Production

After local test works:
1. Deploy backend to Fly.io
2. Update app.js with production URL
3. Deploy frontend to Vercel
4. Test live!

---

**Test now!** 🎯
