# Authorization System

## Overview

The Authorization System provides target whitelisting and scope validation for all offensive security tools in Security Assistant.

## Features

- **Target Whitelisting**: Add domains, IPs, CIDR ranges, and URLs to authorized list
- **Scope Validation**: Automatically check targets before scanning
- **Audit Logging**: Track all authorization actions
- **ToS Enforcement**: Ensure legal compliance before offensive actions
- **Export/Import**: Backup and restore authorization data

## Quick Start

```bash
# Add authorized target
security-assistant authorize --add example.com

# Check authorization
security-assistant authorize --check example.com

# List authorized targets
security-assistant authorize --list

# Remove authorized target
security-assistant authorize --remove example.com

# Accept Terms of Service
security-assistant tos --accept
```

## Target Types

### Domains
```bash
security-assistant authorize --add example.com
security-assistant authorize --add sub.example.com
```

### IP Addresses
```bash
security-assistant authorize --add 192.168.1.1
security-assistant authorize --add 203.0.113.45
```

### CIDR Ranges
```bash
security-assistant authorize --add 192.168.1.0/24
security-assistant authorize --add 203.0.113.0/24
```

### URLs
```bash
security-assistant authorize --add https://example.com
security-assistant authorize --add http://api.example.com
```

## Python API

```python
from security_assistant.offensive.authorization import AuthorizationService

# Initialize service
auth = AuthorizationService()

# Add target
auth.add_authorized_target("example.com", added_by="user@company.com")

# Check authorization
if auth.is_authorized("example.com"):
    print("Authorized!")

# List targets
targets = auth.list_authorized_targets()

# Export data
auth.export_authorization_data(Path("backup.json"))
```

## Audit Logging

All authorization actions are logged:

```python
# Get recent audit logs
logs = auth.get_audit_logs(limit=50)

# Example log entry
{
    "action": "authorize",
    "target_type": "domain",
    "target_value": "example.com",
    "status": "success",
    "timestamp": "2025-12-11T02:29:00.123456",
    "user": "user@company.com",
    "details": "Added domain: example.com"
}
```

## Database

Authorization data is stored in SQLite database:
- Location: `~/.security_assistant/authorization.db`
- Encrypted: No (local storage only)
- Backup: Use `export_authorization_data()` method

## Security Notes

- **Never** share your authorization database
- **Always** backup before making changes
- **Review** audit logs regularly
- **Remove** targets when no longer needed

## Troubleshooting

### Target not authorized
```
Error: Target not authorized: example.com
Solution: security-assistant authorize --add example.com
```

### Database corruption
```
Error: Database error
Solution: Remove ~/.security_assistant/authorization.db and re-add targets
```

### ToS not accepted
```
Error: Terms of Service must be accepted
Solution: security-assistant tos --accept
```

## Best Practices

1. **Start with staging**: Add staging environments first
2. **Use CIDR ranges**: For network segments
3. **Document targets**: Use notes field for context
4. **Review regularly**: Remove unused targets
5. **Backup often**: Export before major changes
