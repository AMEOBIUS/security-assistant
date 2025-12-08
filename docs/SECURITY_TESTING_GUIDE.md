# Security Testing Guide - Session 25

Quick guide to test security improvements implemented in Session 25.

## Prerequisites

```bash
# Start backend
cd backend
podman-compose up -d

# Check logs
podman-compose logs -f api
```

## Test 1: Rate Limiting

### Test Signup Endpoint (5 req/min limit)

```bash
# Should succeed (requests 1-5)
for i in {1..5}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/waitlist \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"test$i@example.com\",\"name\":\"Test User $i\"}"
  echo ""
done

# Should fail with 429 Too Many Requests (request 6)
echo "Request 6 (should fail):"
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"test6@example.com","name":"Test User 6"}'
echo ""

# Wait 60 seconds, then should succeed again
echo "Waiting 60 seconds..."
sleep 60
echo "Request 7 (should succeed after cooldown):"
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"test7@example.com","name":"Test User 7"}'
```

**Expected Output:**
- Requests 1-5: `{"status":"success",...}`
- Request 6: `{"error":"Rate limit exceeded: 5 per 1 minute"}`
- Request 7 (after 60s): `{"status":"success",...}`

### Test Stats Endpoint (20 req/min limit)

```bash
# Should succeed (all 20 requests)
for i in {1..20}; do
  echo "Request $i:"
  curl http://localhost:8000/api/waitlist/count
  echo ""
done

# Should fail (request 21)
echo "Request 21 (should fail):"
curl http://localhost:8000/api/waitlist/count
```

---

## Test 2: Security Headers

```bash
# Check all security headers
curl -I http://localhost:8000/

# Or use verbose mode
curl -v http://localhost:8000/ 2>&1 | grep -E "Strict-Transport-Security|Content-Security-Policy|X-Frame-Options|X-Content-Type-Options|X-XSS-Protection"
```

**Expected Headers:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

## Test 3: Input Validation

### Test Max Length Constraints

```bash
# Should fail - name too long (>100 chars)
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"name\":\"$(python -c 'print("A"*101)')\"}"

# Should fail - role too long (>50 chars)
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"role\":\"$(python -c 'print("B"*51)')\"}"

# Should succeed - within limits
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"valid@example.com","name":"Valid Name","role":"Developer"}'
```

**Expected Output:**
- Too long: `{"detail":[{"type":"string_too_long","loc":["body","name"],...}]}`
- Valid: `{"status":"success",...}`

### Test Input Sanitization

```bash
# Control characters should be removed
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test\u0000User\u0001"}'

# Check database to verify sanitization
podman exec -it security-workstation-db psql -U postgres -d security_workstation -c "SELECT name FROM waitlist_entries WHERE email='test@example.com';"
```

---

## Test 4: Error Handling

### Test Generic Error Messages

```bash
# Trigger database error (duplicate email)
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"duplicate@example.com","name":"First"}'

# Try again with same email
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"duplicate@example.com","name":"Second"}'
```

**Expected Output:**
- First: `{"status":"success",...}`
- Second: `{"detail":"Email already registered"}` (no internal details)

### Check Logs for Detailed Errors

```bash
# View logs to see detailed error info (for debugging)
podman-compose logs api | grep -E "ERROR|WARNING"
```

**Expected Log:**
```
WARNING - Duplicate waitlist signup attempt: duplicate@example.com
```

---

## Test 5: CORS

### Test Allowed Origin

```bash
# Should succeed - allowed origin
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -H "Origin: https://workstation-h49ckizhd-ameobius-projects.vercel.app" \
  -d '{"email":"cors-test@example.com"}'
```

### Test Blocked Origin

```bash
# Should fail - blocked origin
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -H "Origin: https://evil.com" \
  -d '{"email":"cors-test2@example.com"}'
```

**Expected:**
- Allowed origin: Response includes `Access-Control-Allow-Origin` header
- Blocked origin: No CORS headers in response

---

## Test 6: Docker Security

### Verify Non-Root User

```bash
# Check user inside container
podman exec -it security-workstation-api whoami
# Expected: appuser

# Check UID
podman exec -it security-workstation-api id
# Expected: uid=1000(appuser) gid=1000(appuser)
```

### Verify No --reload in Production

```bash
# Check running process
podman exec -it security-workstation-api ps aux | grep uvicorn
# Expected: NO --reload flag
```

---

## Test 7: Structured Logging

### Generate Log Events

```bash
# Successful signup
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"log-test@example.com","name":"Log Test"}'

# Duplicate signup (warning)
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"log-test@example.com","name":"Log Test 2"}'
```

### Check Logs

```bash
podman-compose logs api | tail -20
```

**Expected Log Entries:**
```
INFO - New waitlist signup: log-test@example.com (ID: X)
WARNING - Duplicate waitlist signup attempt: log-test@example.com
```

---

## Test 8: Pre-Commit Hook (Optional)

### Install Hook

```bash
# Configure git to use .githooks
git config core.hooksPath .githooks

# Make hook executable
chmod +x .githooks/pre-commit
```

### Test Secret Detection

```bash
# Create test file with fake secret
echo 'api_key = "sk-test123456789"' > test_secret.py

# Try to commit
git add test_secret.py
git commit -m "Test commit"

# Expected: Commit blocked with error message
# ❌ Potential secret found in test_secret.py

# Clean up
rm test_secret.py
git reset
```

---

## Automated Test Script

Save as `test_security.sh`:

```bash
#!/bin/bash

echo "🔒 Security Testing Suite - Session 25"
echo "======================================"

# Test 1: Rate Limiting
echo ""
echo "Test 1: Rate Limiting (5 req/min)"
for i in {1..6}; do
  echo -n "Request $i: "
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/waitlist \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"test$i@example.com\"}")
  if [ $i -le 5 ]; then
    [ "$STATUS" = "201" ] && echo "✅ PASS" || echo "❌ FAIL (expected 201, got $STATUS)"
  else
    [ "$STATUS" = "429" ] && echo "✅ PASS" || echo "❌ FAIL (expected 429, got $STATUS)"
  fi
done

# Test 2: Security Headers
echo ""
echo "Test 2: Security Headers"
HEADERS=$(curl -sI http://localhost:8000/)
echo -n "HSTS: "
echo "$HEADERS" | grep -q "Strict-Transport-Security" && echo "✅ PASS" || echo "❌ FAIL"
echo -n "CSP: "
echo "$HEADERS" | grep -q "Content-Security-Policy" && echo "✅ PASS" || echo "❌ FAIL"
echo -n "X-Frame-Options: "
echo "$HEADERS" | grep -q "X-Frame-Options" && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Input Validation
echo ""
echo "Test 3: Input Validation"
echo -n "Max length (name > 100): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"name\":\"$(python -c 'print("A"*101)')\"}")
[ "$STATUS" = "422" ] && echo "✅ PASS" || echo "❌ FAIL (expected 422, got $STATUS)"

echo ""
echo "======================================"
echo "✅ Security testing complete!"
```

Run:
```bash
chmod +x test_security.sh
./test_security.sh
```

---

## Cleanup

```bash
# Stop services
podman-compose down

# Remove test data
podman exec -it security-workstation-db psql -U postgres -d security_workstation -c "DELETE FROM waitlist_entries WHERE email LIKE 'test%@example.com';"
```

---

## Troubleshooting

### Rate Limiting Not Working
```bash
# Check if slowapi is installed
podman exec -it security-workstation-api pip list | grep slowapi

# Check logs for rate limiter initialization
podman-compose logs api | grep -i "limiter"
```

### Security Headers Missing
```bash
# Check if middleware is loaded
podman-compose logs api | grep -i "middleware"

# Verify main.py changes
podman exec -it security-workstation-api cat app/main.py | grep -A 5 "add_security_headers"
```

### Input Validation Not Working
```bash
# Check Pydantic version
podman exec -it security-workstation-api pip show pydantic

# Verify waitlist.py changes
podman exec -it security-workstation-api cat app/routers/waitlist.py | grep -A 3 "Field"
```

---

**Related Documentation:**
- [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md)
- [SESSION_25_SUMMARY.md](SESSION_25_SUMMARY.md)
