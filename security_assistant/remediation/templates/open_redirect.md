# Open Redirect Remediation

## Description
Open redirect vulnerabilities occur when an application redirects users to a URL provided in a parameter without validation. Attackers use this to phish users by redirecting them from a trusted site to a malicious one.

## Remediation
1.  **Avoid User Input in Redirects**: Use indirect references (IDs/Tokens) mapped to internal URLs.
2.  **Validate URLs**: Ensure the redirect URL matches a strict allowlist of trusted domains.
3.  **Local Redirects Only**: Restrict redirects to local paths (starting with `/` but not `//`).
4.  **Notify Users**: Display a warning page before redirecting to an external site.
