# Legal Framework

## Overview

Security Assistant's offensive security tools require legal compliance and ethical use. This document explains the legal framework.

## Terms of Service

### Key Points

1. **Authorization Required**: You must have explicit permission to test targets
2. **No Unauthorized Testing**: Never test systems you don't own or control
3. **Compliance**: Follow all applicable laws and regulations
4. **Liability**: You are responsible for your actions
5. **Data Collection**: We collect audit logs for security purposes

### Acceptance

```bash
# Accept ToS
security-assistant tos --accept

# Check ToS status
security-assistant tos --status
```

## Ethical Guidelines

### Principles

1. **Authorization First**: Always get permission before testing
2. **Minimize Impact**: Use least intrusive methods
3. **Transparency**: Document and report your actions
4. **Professionalism**: Follow industry standards
5. **Continuous Learning**: Stay updated on best practices

### Red Flags

**STOP** if you encounter:
- Production systems without backup
- Critical infrastructure (healthcare, finance)
- Personal or sensitive data
- Systems with unclear ownership

## Compliance Checklist

### Before Testing
- [ ] Obtain written authorization
- [ ] Add target to whitelist
- [ ] Review scope and limitations
- [ ] Set up monitoring
- [ ] Notify stakeholders

### During Testing
- [ ] Start with non-intrusive scans
- [ ] Document all actions
- [ ] Monitor for unexpected impacts
- [ ] Escalate issues promptly
- [ ] Follow principle of least privilege

### After Testing
- [ ] Generate comprehensive reports
- [ ] Remove test artifacts
- [ ] Review audit logs
- [ ] Update documentation
- [ ] Share lessons learned

## Legal Considerations

### Laws and Regulations

- **Computer Fraud and Abuse Act (CFAA)**: US anti-hacking law
- **General Data Protection Regulation (GDPR)**: EU data protection
- **Computer Misuse Act**: UK cybercrime law
- **Local laws**: Vary by jurisdiction

### Penalties

Unauthorized testing may result in:
- Criminal charges
- Civil lawsuits
- Professional sanctions
- Reputation damage

## Reporting

### Vulnerability Disclosure

1. **Document**: All findings with evidence
2. **Report**: To system owner promptly
3. **Coordinate**: Fix and disclosure timeline
4. **Respect**: Embargo periods and requests

### Incident Response

If something goes wrong:
1. **Stop**: Immediately cease testing
2. **Document**: What happened
3. **Report**: To stakeholders
4. **Remediate**: Fix any damage
5. **Review**: Prevent recurrence

## Resources

### Legal
- [CFAA Guide](https://www.justice.gov/criminal-cybersecurity/cybersecurity-unit)
- [GDPR Official Text](https://gdpr-info.eu/)
- [OWASP Legal FAQ](https://owasp.org/www-project-legal/)

### Ethical
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST SP 800-115](https://csrc.nist.gov/publications/detail/sp/800-115/final)
- [PTES Technical Guidelines](http://www.pentest-standard.org/)

### Training
- [Offensive Security Courses](https://www.offensive-security.com/)
- [SANS Institute](https://www.sans.org/)
- [Hack The Box](https://www.hackthebox.com/)

## FAQ

### Q: Can I test my employer's systems?
**A**: Only with explicit written permission from authorized personnel.

### Q: What about public bug bounty programs?
**A**: Yes, if the program explicitly allows your testing methods.

### Q: Can I test my own personal systems?
**A**: Yes, you own them and control them.

### Q: What should I do if I find something unexpected?
**A**: Stop immediately and report to the system owner.

### Q: How often should I review my authorization?
**A**: At least quarterly, or when targets change.

## Support

For legal questions:
- Consult your organization's legal team
- Review applicable laws and regulations
- When in doubt, ask for help

**Last Updated:** December 11, 2025
