# Email Service - Quick Start

## 🚀 Quick Setup (5 minutes)

### 1. Get Gmail App Password

```bash
# Open in browser
https://myaccount.google.com/apppasswords
```

1. Enable 2FA if not enabled
2. Create App Password for "Mail" → "Other (Security Workstation)"
3. Copy 16-character password (remove spaces)

### 2. Configure Credentials

**Option A: Doppler (Production)**

```bash
doppler secrets set SMTP_USERNAME="your-email@gmail.com"
doppler secrets set SMTP_PASSWORD="abcdefghijklmnop"
```

**Option B: .env (Development)**

```bash
cd backend
echo 'SMTP_USERNAME=your-email@gmail.com' >> .env
echo 'SMTP_PASSWORD=abcdefghijklmnop' >> .env
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Test Email Sending

```bash
# With Doppler
doppler run -- python scripts/test_email.py

# Without Doppler
python scripts/test_email.py
```

Expected output:
```
✅ Basic email sent successfully!
✅ Welcome email sent successfully!
🎉 All tests passed!
```

## 📧 Usage in Code

```python
from app.services.email import send_welcome_email, send_notification_email

# Send welcome email to new user
await send_welcome_email(
    to_email="user@example.com",
    name="John Doe"
)

# Send notification to admin
await send_notification_email(
    subject="New Signup",
    message="User joined waitlist"
)
```

## 🔧 Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_USERNAME` | ✅ Yes | - | Gmail address |
| `SMTP_PASSWORD` | ✅ Yes | - | Gmail App Password |
| `SMTP_FROM_EMAIL` | ❌ No | `SMTP_USERNAME` | Sender email |
| `SMTP_FROM_NAME` | ❌ No | `Security Workstation` | Sender name |
| `SMTP_HOST` | ❌ No | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | ❌ No | `587` | SMTP port (TLS) |

## 📊 Gmail Limits

- **Free Gmail:** 500 emails/day
- **Google Workspace:** 2,000 emails/day

## 🐛 Troubleshooting

### "Username and Password not accepted"

```bash
# 1. Verify 2FA is enabled
# 2. Generate new App Password
# 3. Remove spaces from password
doppler secrets set SMTP_PASSWORD="abcdefghijklmnop"
```

### "Connection timeout"

```bash
# Check firewall allows port 587
# Try alternative port 465 (SSL)
doppler secrets set SMTP_PORT="465"
```

### Emails going to spam

- Use Google Workspace for better deliverability
- Set up SPF/DKIM records for your domain
- Warm up email sending (start with low volume)

## 📚 Full Documentation

- [Gmail SMTP Setup Guide](docs/GMAIL_SMTP_SETUP.md)
- [Email Service API](backend/app/services/email.py)
- [Tests](backend/tests/test_email.py)

## 🔄 Migration from Resend

Already done! ✅

- ✅ Removed `resend` dependency
- ✅ Added `aiosmtplib` for Gmail SMTP
- ✅ Updated email service to use SMTP
- ✅ Updated configuration
- ✅ Created tests and documentation

## 🎯 Next Steps

1. ✅ Test email sending in development
2. ⏳ Configure production Gmail account
3. ⏳ Set up email monitoring/logging
4. ⏳ Implement email queue for high volume
5. ⏳ Consider transactional email service for scale
