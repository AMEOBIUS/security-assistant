# Meta-Security Protection

## 🛡️ Overview

The Security Workstation implements **meta-security** protection to prevent attacks where the security tools themselves become attack vectors. This addresses the "penetration test inception" scenario identified by DROID AI.

## 🔴 Vulnerabilities Fixed

### 1. Scanner-on-Scanner Attack

**Problem:** Compromised scanner plugins could escalate to control the entire orchestration system.

**Solution:** `ScannerIntegrityValidator`
- Whitelist of allowed scanner classes
- Method signature verification
- Import path validation
- Runtime behavior monitoring

```python
from security_assistant.orchestrator import ScanOrchestrator

# Meta-security enabled by default
orchestrator = ScanOrchestrator(enable_meta_security=True)

# Only whitelisted scanners are allowed
orchestrator.enable_scanner(ScannerType.BANDIT)  # ✓ Allowed
orchestrator.enable_scanner(ScannerType.CUSTOM)  # ✗ Rejected
```

### 2. Configuration Injection Loop

**Problem:** CLI loads configurations from directories it scans, creating execution vulnerabilities.

**Solution:** `ConfigurationSandbox`
- Separate config directories from scan targets
- Path traversal prevention
- Config file integrity verification
- Restricted config file locations

```python
from security_assistant.config import load_config

# Automatically validates config path
config = load_config("security-assistant.yaml")  # ✓ Safe

# Rejects configs in forbidden locations
config = load_config(".git/malicious.yaml")  # ✗ Rejected
```

### 3. Cache Poisoning Cascade

**Problem:** Performance cache could be manipulated to hide or fabricate vulnerabilities.

**Solution:** `CacheIntegrityValidator`
- HMAC-based cache verification
- Timestamp validation
- Cache entry expiration
- Tamper detection

```python
from security_assistant.security_validator import MetaSecurityValidator

validator = MetaSecurityValidator()

# Sign cache entry
data = {'findings': [...]}
signed = validator.sign_cache_entry(data)

# Verify integrity
result = validator.validate_cache_entry(signed)
if not result.is_valid:
    print("Cache tampering detected!")
```

## 📋 Usage

### Automatic Protection (Recommended)

Meta-security is **enabled by default** in all components:

```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.config import load_config

# Orchestrator validates all scanners
orchestrator = ScanOrchestrator()  # meta-security ON
orchestrator.enable_scanner(ScannerType.BANDIT)

# Config loader validates paths
config = load_config("config.yaml")  # path validation ON
```

### Manual Validation

For custom scenarios:

```python
from security_assistant.security_validator import (
    ScannerIntegrityValidator,
    ConfigurationSandbox,
    CacheIntegrityValidator,
)

# Validate scanner
scanner_validator = ScannerIntegrityValidator(strict_mode=True)
result = scanner_validator.validate_scanner(my_scanner)

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")

# Validate config path
config_sandbox = ConfigurationSandbox()
result = config_sandbox.validate_config_path(Path("config.yaml"))

# Validate cache
cache_validator = CacheIntegrityValidator()
signed_data = cache_validator.sign_cache_entry(data)
result = cache_validator.verify_cache_entry(signed_data)
```

### Disable Meta-Security (Not Recommended)

Only for testing or development:

```python
# Disable in orchestrator
orchestrator = ScanOrchestrator(enable_meta_security=False)

# Disable in config loader
config = SecurityAssistantConfig.load("config.yaml", validate_security=False)
```

## 🔍 Validation Details

### Scanner Validation

**Checks performed:**
1. ✅ Scanner class in whitelist
2. ✅ Loaded from expected module path
3. ✅ Has required methods (`scan_directory`, `scan_file`, etc.)
4. ✅ No forbidden methods (`exec`, `eval`, `system`, etc.)
5. ✅ Method signatures match expected patterns
6. ✅ Source code location verification

**Whitelisted Scanners:**
- `BanditScanner` from `security_assistant.scanners.bandit_scanner`
- `SemgrepScanner` from `security_assistant.scanners.semgrep_scanner`
- `TrivyScanner` from `security_assistant.scanners.trivy_scanner`

### Configuration Validation

**Checks performed:**
1. ✅ File exists and is readable
2. ✅ Path is within project root
3. ✅ Not in forbidden directories (`.git`, `.venv`, `node_modules`, etc.)
4. ✅ In recommended config locations (`.`, `.config`, `config`)
5. ✅ Valid file extension (`.yaml`, `.yml`, `.json`)
6. ✅ File integrity (hash verification on reload)

**Allowed Config Locations:**
- Project root: `./security-assistant.yaml`
- Config directory: `./.config/security-assistant.yaml`
- Config directory: `./config/security-assistant.yaml`

**Forbidden Config Locations:**
- `.git/` - Git internals
- `.venv/`, `venv/` - Virtual environments
- `node_modules/` - Node dependencies
- `__pycache__/` - Python cache
- `build/`, `dist/` - Build artifacts

### Cache Validation

**Checks performed:**
1. ✅ HMAC signature verification
2. ✅ Timestamp validation
3. ✅ TTL (time-to-live) check
4. ✅ Version compatibility
5. ✅ Required fields present

**Cache Entry Structure:**
```json
{
  "data": { ... },
  "timestamp": "2025-12-01T10:00:00",
  "version": "1.0",
  "signature": "abc123..."
}
```

## 🧪 Testing

Run meta-security tests:

```bash
# All meta-security tests
pytest tests/test_meta_security.py -v

# Specific test class
pytest tests/test_meta_security.py::TestScannerIntegrityValidator -v

# Test orchestrator integration
pytest tests/test_meta_security.py::TestOrchestratorIntegration -v
```

## 🚨 Security Warnings

### When Validation Fails

**Scanner validation failure:**
```
🚨 Scanner validation failed for bandit:
  - Scanner 'MaliciousScanner' is not in whitelist
  - Scanner contains potentially dangerous methods: ['exec', 'eval']
```

**Config validation failure:**
```
⚠️  Config validation warning: Config file in forbidden location: .git/config.yaml
⚠️  Config validation warning: Config file has been modified since last validation
```

**Cache validation failure:**
```
❌ Cache entry signature verification failed (possible tampering)
⚠️  Cache entry expired (age: 25.3h, TTL: 24.0h)
```

## 📊 Validation Results

All validation methods return `SecurityValidationResult`:

```python
@dataclass
class SecurityValidationResult:
    is_valid: bool              # Overall validation status
    errors: List[str]           # Blocking errors
    warnings: List[str]         # Non-blocking warnings
    metadata: Dict[str, Any]    # Additional information
```

**Example:**
```python
result = validator.validate_scanner(scanner)

if result.is_valid:
    print("✓ Scanner validated successfully")
else:
    print("✗ Validation failed:")
    for error in result.errors:
        print(f"  - {error}")

for warning in result.warnings:
    print(f"⚠️  {warning}")
```

## 🔧 Configuration

### Strict Mode

Control validation strictness:

```python
# Strict mode (recommended for production)
validator = ScannerIntegrityValidator(strict_mode=True)
# Only whitelisted scanners allowed

# Permissive mode (for development)
validator = ScannerIntegrityValidator(strict_mode=False)
# Custom scanners allowed if they have required methods
```

### Cache TTL

Configure cache expiration:

```python
# Default: 24 hours
validator = CacheIntegrityValidator(ttl_hours=24)

# Shorter TTL for sensitive data
validator = CacheIntegrityValidator(ttl_hours=1)

# Longer TTL for stable data
validator = CacheIntegrityValidator(ttl_hours=168)  # 1 week
```

### Custom Secret Key

Provide custom HMAC key for cache:

```python
import secrets

# Generate secure key
secret_key = secrets.token_bytes(32)

# Use custom key
validator = CacheIntegrityValidator(secret_key=secret_key)
```

## 🎯 Best Practices

1. **Always enable meta-security in production**
   ```python
   orchestrator = ScanOrchestrator(enable_meta_security=True)
   ```

2. **Store configs in standard locations**
   ```
   ✓ ./security-assistant.yaml
   ✓ ./.config/security-assistant.yaml
   ✗ ./src/config.yaml
   ```

3. **Validate cache entries before use**
   ```python
   result = validator.validate_cache_entry(cached_data)
   if result.is_valid:
       use_cached_data()
   else:
       rescan()
   ```

4. **Monitor validation warnings**
   ```python
   for warning in result.warnings:
       logger.warning(f"Meta-security: {warning}")
   ```

5. **Use strict mode for scanners**
   ```python
   validator = ScannerIntegrityValidator(strict_mode=True)
   ```

## 🔗 Related

- [Security Architecture](../docs/architecture.md)
- [Scanner Development](../docs/scanner-development.md)
- [Configuration Guide](../docs/configuration.md)
- [Testing Guide](../docs/testing.md)

## 📝 Implementation Details

**Files:**
- `security_assistant/security_validator.py` - Core validation logic
- `security_assistant/orchestrator.py` - Scanner validation integration
- `security_assistant/config.py` - Config validation integration
- `tests/test_meta_security.py` - Comprehensive test suite

**Dependencies:**
- `hashlib` - SHA-256 hashing
- `hmac` - HMAC signatures
- `inspect` - Method signature validation
- `pathlib` - Path manipulation

## 🎓 Learn More

This meta-security implementation was inspired by the "Quantum-Entangled Security Scanning" concept proposed by DROID AI, which identified circular dependencies and self-referential vulnerabilities in the security workstation architecture.

The system implements defense-in-depth by validating:
1. **What** is being executed (scanner integrity)
2. **Where** configuration comes from (config sandboxing)
3. **When** cached data is valid (cache integrity)

This creates a "security workstation that secures itself" - preventing the tools from becoming attack vectors.
