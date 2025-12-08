# Server-Side Request Forgery (SSRF) Remediation

## Description
SSRF flaws occur whenever a web application is fetching a remote resource without validating the user-supplied URL. It allows an attacker to coerce the application to send a crafted request to an unexpected destination, often internal systems.

## Remediation
1. **Allowlist Domains**: Only allow requests to a strict allowlist of domains/IPs.
2. **Disable Redirects**: Disable HTTP redirects or strictly validate the redirect URL.
3. **Block Internal IP Ranges**: Deny requests to private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, etc.).
4. **Use Network-Level Controls**: Use firewall rules to restrict outbound traffic.
