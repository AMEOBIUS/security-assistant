# Cross-Site Request Forgery (CSRF) Remediation

## Description
Cross-Site Request Forgery (CSRF) is an attack that forces an end user to execute unwanted actions on a web application in which they're currently authenticated.

## Remediation
1. **Anti-CSRF Tokens**: Include a unique, unpredictable, and secret token in all state-changing requests (POST, PUT, DELETE).
2. **SameSite Cookie Attribute**: Set the `SameSite` attribute on session cookies to `Strict` or `Lax`.
3. **Verify Origin**: Check the `Origin` and `Referer` headers for state-changing requests.
4. **Use Framework Protection**: Most modern web frameworks (Django, Flask-WTF, Rails, Spring) have built-in CSRF protection. Enable it.
