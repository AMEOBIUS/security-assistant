# Email Integration Guide - Resend

## Overview

Security Workstation uses **Resend** for transactional emails (welcome emails, notifications).

**Why Resend?**
- ✅ Free tier: 100 emails/day, 3,000/month
- ✅ Simple API (one line of code)
- ✅ Modern developer experience
- ✅ No credit card required for free tier
- ✅ Better deliverability than SendGrid/Mailgun

---

## Setup (5 minutes)

### Step 1: Create Resend Account

1. Go to https://resend.com
2. Sign up (free, no credit card)
3. Verify your email

### Step 2: Get API Key

1. Go to https://resend.com/api-keys
2. Click "Create API Key"
3. Name: `security-workstation-dev`
4. Permissions: "Sending access"
5. Copy the key (starts with `re_...`)

### Step 3: Add to Doppler

```bash
# Add API key to Doppler
doppler secrets set RESEND_API_KEY="re_..." --config dev

# Optional: Set custom from email (after domain verification)
doppler secrets set RESEND_FROM_EMAIL="Security Workstation <noreply@securityworkstation.ai>"
```

### Step 4: Test

```bash
# Restart backend
cd backend
doppler run -- uvicorn app.main:app --reload

# Test signup (should send email)
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"your-real-email@example.com","name":"Test User"}'

# Check your inbox!
```

---

## Domain Verification (Production)

### For Production Emails

To send from `@securityworkstation.ai`:

1. **Buy domain** (if not already owned)
   - Namecheap, Cloudflare, etc.
   - ~$12/year

2. **Add domain to Resend**
   - Go to https://resend.com/domains
   - Click "Add Domain"
   - Enter: `securityworkstation.ai`

3. **Add DNS records**
   - Resend will show required DNS records
   - Add to your DNS provider:
     - SPF record
     - DKIM record
     - DMARC record (optional)

4. **Verify domain**
   - Click "Verify" in Resend dashboard
   - Wait 5-10 minutes for DNS propagation

5. **Update Doppler**
   ```bash
   doppler secrets set RESEND_FROM_EMAIL="Security Workstation <noreply@securityworkstation.ai>" --config production
   ```

---

## Email Templates

### Welcome Email (Implemented)

**Sent when:** User signs up for waitlist

**Content:**
- Welcome message
- What's next (launch date, free months)
- Call to action (GitHub, landing page)
- Contact info

**Template:** `backend/app/services/email.py` → `send_welcome_email()`

### Notification Email (Implemented)

**Sent when:** New waitlist signup

**To:** Admin (hello@securityworkstation.ai)

**Content:**
- Email, name, role, source
- Quick notification for monitoring

**Template:** `backend/app/services/email.py` → `send_notification_email()`

---

## Customization

### Update Welcome Email

Edit `backend/app/services/email.py`:

```python
async def send_welcome_email(to_email: str, name: str = "") -> bool:
    # ... existing code ...
    
    params = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": "Your Custom Subject",
        "html": """
        <!-- Your custom HTML template -->
        """
    }
```

### Add New Email Type

```python
async def send_beta_invite_email(to_email: str, invite_code: str) -> bool:
    """Send beta invite with access code"""
    
    params = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": "Your Beta Invite is Ready! 🎉",
        "html": f"""
        <html>
        <body>
            <h1>You're Invited!</h1>
            <p>Your beta access code: <strong>{invite_code}</strong></p>
            <a href="https://app.securityworkstation.ai/signup?code={invite_code}">
                Activate Account
            </a>
        </body>
        </html>
        """
    }
    
    email = resend.Emails.send(params)
    return True
```

---

## Testing

### Test Welcome Email

```bash
# Sign up with your real email
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@gmail.com","name":"Test User","role":"developer"}'

# Check inbox (should arrive in <10 seconds)
```

### Test Without Resend (Fallback)

```bash
# Remove API key temporarily
doppler secrets delete RESEND_API_KEY --config dev

# Signup should still work (email skipped)
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Check logs
# Should see: "Resend API key not configured, skipping email"
```

---

## Monitoring

### Check Email Logs

**Resend Dashboard:**
- https://resend.com/emails
- See all sent emails
- Delivery status
- Open/click rates (if tracking enabled)

**Application Logs:**
```bash
# View backend logs
doppler run -- uvicorn app.main:app --reload

# Look for:
# INFO - Welcome email sent to user@example.com (ID: xxx)
# ERROR - Failed to send welcome email: ...
```

---

## Pricing

### Free Tier (Current)
- ✅ 100 emails/day
- ✅ 3,000 emails/month
- ✅ All features
- ✅ No credit card required

**Sufficient for:** 100 signups/day

### Paid Plans (If Needed)

| Plan | Price | Emails/Month |
|------|-------|--------------|
| **Free** | $0 | 3,000 |
| **Pro** | $20/mo | 50,000 |
| **Business** | $80/mo | 100,000 |

**When to upgrade:** >100 signups/day

---

## Troubleshooting

### Email Not Sending

**Check API key:**
```bash
doppler secrets get RESEND_API_KEY
```

**Check logs:**
```bash
# Should see error message
doppler run -- uvicorn app.main:app --reload
# Look for: "Failed to send welcome email"
```

**Test API key:**
```python
import resend
resend.api_key = "re_..."

email = resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": ["your-email@example.com"],
    "subject": "Test",
    "html": "<p>Test email</p>"
})

print(email)
```

### Email in Spam

**Solutions:**
1. Verify domain (SPF, DKIM, DMARC)
2. Use custom domain (not @resend.dev)
3. Warm up sending (start slow, increase gradually)
4. Add unsubscribe link

### Rate Limit Exceeded

**Free tier:** 100 emails/day

**Solutions:**
1. Upgrade to Pro ($20/mo for 50k/month)
2. Queue emails (send in batches)
3. Use multiple API keys (not recommended)

---

## Best Practices

### 1. Always Handle Failures

```python
try:
    await send_welcome_email(email, name)
except Exception as e:
    # Don't fail the request if email fails
    logger.error(f"Email failed: {e}")
```

### 2. Use Templates

Create reusable HTML templates:
```python
# backend/app/templates/emails/welcome.html
```

### 3. Track Metrics

```python
# Log email events
logger.info(f"Email sent: {email_id}")
logger.info(f"Email opened: {email_id}")
logger.info(f"Link clicked: {email_id}")
```

### 4. Test Thoroughly

- Test with real email addresses
- Check spam folder
- Test on mobile devices
- Verify links work

---

## Alternatives

If Resend doesn't work for you:

### SendGrid
- Free: 100 emails/day
- More complex API
- Better for high volume

### Mailgun
- Free: 5,000 emails/month
- Good deliverability
- More expensive

### ConvertKit
- Free: 1,000 subscribers
- Marketing automation
- Overkill for transactional emails

**Recommendation:** Stick with Resend for simplicity.

---

## Next Steps

1. ✅ Sign up for Resend
2. ✅ Get API key
3. ✅ Add to Doppler
4. ✅ Test welcome email
5. ⏳ Verify domain (for production)
6. ⏳ Customize email templates
7. ⏳ Add more email types (beta invite, etc.)

---

## Support

- **Resend Docs:** https://resend.com/docs
- **Resend API Reference:** https://resend.com/docs/api-reference
- **Resend Status:** https://status.resend.com

---

**Questions?** Check the code in `backend/app/services/email.py`
