# Gmail SMTP Setup Guide

This guide explains how to configure Gmail SMTP for sending emails from Security Workstation.

## 📋 Prerequisites

- Gmail account (free or Google Workspace)
- 2-Factor Authentication enabled on Gmail

## 🔧 Setup Steps

### 1. Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the setup wizard to enable 2FA

### 2. Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select app: **Mail**
3. Select device: **Other (Custom name)**
4. Enter name: **Security Workstation**
5. Click **Generate**
6. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 3. Configure Environment Variables

#### Option A: Using Doppler (Recommended)

```bash
# Set Gmail credentials in Doppler
doppler secrets set SMTP_USERNAME="your-email@gmail.com"
doppler secrets set SMTP_PASSWORD="abcdefghijklmnop"  # Remove spaces
doppler secrets set SMTP_FROM_EMAIL="your-email@gmail.com"
doppler secrets set SMTP_FROM_NAME="Security Workstation"
```

#### Option B: Using .env File (Local Development)

Create `backend/.env`:

```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Security Workstation
```

### 4. Test Email Sending

```python
from app.services.email import send_welcome_email

# Test welcome email
await send_welcome_email(
    to_email="test@example.com",
    name="Test User"
)
```

## 📊 Gmail Sending Limits

| Account Type | Daily Limit |
|--------------|-------------|
| Free Gmail | 500 emails/day |
| Google Workspace | 2,000 emails/day |

## 🔒 Security Best Practices

1. **Never commit App Passwords** to version control
2. **Use Doppler** for production secrets management
3. **Rotate App Passwords** every 90 days
4. **Monitor Gmail activity** for suspicious logins
5. **Use dedicated email** for production (not personal Gmail)

## 🐛 Troubleshooting

### Error: "Username and Password not accepted"

**Solution:** 
- Verify 2FA is enabled
- Regenerate App Password
- Remove spaces from password
- Check username is full email address

### Error: "SMTPAuthenticationError"

**Solution:**
- Ensure App Password (not regular password) is used
- Check SMTP credentials in Doppler/env

### Error: "Connection timeout"

**Solution:**
- Check firewall allows port 587
- Verify internet connection
- Try port 465 (SSL) instead of 587 (TLS)

### Emails going to spam

**Solution:**
- Set up SPF record for your domain
- Set up DKIM signing
- Use Google Workspace for better deliverability
- Warm up email sending (start with low volume)

## 🔄 Migration from Resend

If migrating from Resend:

1. ✅ Update `requirements.txt` (remove `resend`, add `aiosmtplib`)
2. ✅ Update `app/config.py` (replace Resend config with SMTP)
3. ✅ Update `app/services/email.py` (use SMTP instead of Resend API)
4. ✅ Update `.env.example` with SMTP variables
5. ✅ Set SMTP credentials in Doppler
6. ✅ Test email sending
7. ✅ Remove Resend API key from Doppler

## 📚 Additional Resources

- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [App Passwords Guide](https://support.google.com/accounts/answer/185833)
- [aiosmtplib Documentation](https://aiosmtplib.readthedocs.io/)

## 🎯 Next Steps

After setup:

1. Test email sending in development
2. Configure production Gmail account
3. Set up email monitoring/logging
4. Implement email queue for high volume
5. Consider transactional email service for scale (SendGrid, Mailgun)
