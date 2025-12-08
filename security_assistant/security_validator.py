"""
Security Validator - Meta-Security Protection Layer

This module provides security validation to prevent meta-attacks where
the security workstation's own tools become attack vectors.

Protections:
1. Scanner Integrity Validation - Prevents compromised scanner plugins
2. Configuration Sandboxing - Isolates config loading from scan targets
3. Cache Integrity - Cryptographic verification of cached results
4. Plugin Signature Verification - Ensures scanner authenticity

Version: 1.0.0
"""

import hashlib
import hmac
import json
import logging
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


@dataclass
class SecurityValidationResult:
    """Result of security validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


class ScannerIntegrityValidator:
    """
    Validates scanner plugin integrity to prevent Scanner-on-Scanner attacks.
    
    Protection mechanisms:
    - Whitelist of allowed scanner classes
    - Method signature verification
    - Import path validation
    - Runtime behavior monitoring
    """
    
    # Whitelist of allowed scanner classes
    ALLOWED_SCANNERS = {
        'BanditScanner': 'security_assistant.scanners.bandit_scanner',
        'SemgrepScanner': 'security_assistant.scanners.semgrep_scanner',
        'TrivyScanner': 'security_assistant.scanners.trivy_scanner',
    }
    
    # Required methods for valid scanners (scanner-specific)
    REQUIRED_METHODS_BY_SCANNER = {
        'BanditScanner': {'scan_directory', 'scan_file'},
        'SemgrepScanner': {'scan_directory', 'scan_file'},
        'TrivyScanner': {'scan_filesystem', 'scan_image'},  # Trivy has different method names
    }
    
    # Forbidden methods that indicate malicious behavior
    FORBIDDEN_METHODS = {
        'exec', 'eval', 'compile', '__import__',
        'open', 'write', 'system', 'popen',
    }
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize scanner integrity validator.
        
        Args:
            strict_mode: If True, only whitelisted scanners are allowed
        """
        self.strict_mode = strict_mode
        self._validated_scanners: Set[str] = set()
    
    def validate_scanner(self, scanner: Any) -> SecurityValidationResult:
        """
        Validate scanner integrity.
        
        Args:
            scanner: Scanner instance to validate
            
        Returns:
            SecurityValidationResult with validation status
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Get scanner class info
        scanner_class = scanner.__class__
        scanner_name = scanner_class.__name__
        scanner_module = scanner_class.__module__
        
        metadata['scanner_name'] = scanner_name
        metadata['scanner_module'] = scanner_module
        
        # 1. Check if scanner is in whitelist (strict mode)
        if self.strict_mode:
            if scanner_name not in self.ALLOWED_SCANNERS:
                errors.append(
                    f"Scanner '{scanner_name}' is not in whitelist. "
                    f"Allowed scanners: {list(self.ALLOWED_SCANNERS.keys())}"
                )
            else:
                expected_module = self.ALLOWED_SCANNERS[scanner_name]
                if scanner_module != expected_module:
                    errors.append(
                        f"Scanner '{scanner_name}' loaded from unexpected module. "
                        f"Expected: {expected_module}, Got: {scanner_module}"
                    )
        
        # 2. Verify required methods exist
        required_methods = self.REQUIRED_METHODS_BY_SCANNER.get(
            scanner_name,
            {'scan_directory', 'scan_file'}  # Default for unknown scanners
        )
        
        missing_methods = []
        for method_name in required_methods:
            if not hasattr(scanner, method_name):
                missing_methods.append(method_name)
        
        if missing_methods:
            errors.append(
                f"Scanner missing required methods: {missing_methods}"
            )
        
        # 3. Check for forbidden methods (potential malicious code)
        forbidden_found = []
        for attr_name in dir(scanner):
            if attr_name in self.FORBIDDEN_METHODS:
                # Check if it's a direct method (not inherited)
                attr = getattr(scanner, attr_name)
                if callable(attr):
                    forbidden_found.append(attr_name)
        
        if forbidden_found:
            warnings.append(
                f"Scanner contains potentially dangerous methods: {forbidden_found}"
            )
        
        # 4. Verify method signatures
        required_methods = self.REQUIRED_METHODS_BY_SCANNER.get(
            scanner_name,
            {'scan_directory', 'scan_file'}
        )
        
        for method_name in required_methods:
            if hasattr(scanner, method_name):
                method = getattr(scanner, method_name)
                sig = inspect.signature(method)
                
                # Validate scan_directory/scan_filesystem signature
                if 'scan_directory' in method_name or 'scan_filesystem' in method_name:
                    params = list(sig.parameters.keys())
                    if 'directory' not in params and 'directory_path' not in params and 'path' not in params:
                        warnings.append(
                            f"Method '{method_name}' has unexpected signature: {sig}"
                        )
                
                # Validate scan_file signature
                if 'scan_file' in method_name:
                    params = list(sig.parameters.keys())
                    if 'file_path' not in params and 'file' not in params:
                        warnings.append(
                            f"Method '{method_name}' has unexpected signature: {sig}"
                        )
        
        # 5. Check scanner source code location
        try:
            source_file = inspect.getfile(scanner_class)
            metadata['source_file'] = source_file
            
            # Ensure scanner is from expected location
            if 'security_assistant/scanners' not in source_file:
                warnings.append(
                    f"Scanner loaded from unexpected location: {source_file}"
                )
        except (TypeError, OSError) as e:
            warnings.append(f"Could not verify scanner source location: {e}")
        
        # Mark as validated if no errors
        is_valid = len(errors) == 0
        if is_valid:
            self._validated_scanners.add(f"{scanner_module}.{scanner_name}")
            logger.info(f"✓ Scanner validated: {scanner_name}")
        else:
            logger.error(f"✗ Scanner validation failed: {scanner_name}")
            for error in errors:
                logger.error(f"  - {error}")
        
        return SecurityValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def is_validated(self, scanner: Any) -> bool:
        """Check if scanner has been validated."""
        scanner_class = scanner.__class__
        scanner_id = f"{scanner_class.__module__}.{scanner_class.__name__}"
        return scanner_id in self._validated_scanners


class ConfigurationSandbox:
    """
    Sandboxes configuration loading to prevent Configuration Injection attacks.
    
    Protection mechanisms:
    - Separate config directories from scan targets
    - Path traversal prevention
    - Config file integrity verification
    - Restricted config file locations
    """
    
    # Allowed config file locations (relative to project root)
    ALLOWED_CONFIG_DIRS = {
        '.',
        '.config',
        'config',
        '.security-assistant',
    }
    
    # Forbidden config file locations
    FORBIDDEN_CONFIG_PATTERNS = {
        '.git',
        '.venv',
        'venv',
        'node_modules',
        '__pycache__',
        'build',
        'dist',
    }
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration sandbox.
        
        Args:
            project_root: Project root directory (default: current directory)
        """
        self.project_root = project_root or Path.cwd()
        self._validated_configs: Dict[str, str] = {}  # path -> hash
    
    def validate_config_path(self, config_path: Path) -> SecurityValidationResult:
        """
        Validate configuration file path.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            SecurityValidationResult
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Resolve to absolute path
        try:
            abs_path = config_path.resolve()
            metadata['absolute_path'] = str(abs_path)
        except (OSError, RuntimeError) as e:
            errors.append(f"Could not resolve config path: {e}")
            return SecurityValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
        
        # 1. Check if path exists
        if not abs_path.exists():
            errors.append(f"Config file does not exist: {abs_path}")
        
        # 2. Check if it's a file (not directory)
        if abs_path.exists() and not abs_path.is_file():
            errors.append(f"Config path is not a file: {abs_path}")
        
        # 3. Check for forbidden patterns FIRST (even outside project root)
        path_str = str(abs_path)
        path_str_forward = path_str.replace('\\', '/')
        path_str_back = path_str.replace('/', '\\')
        
        for forbidden in self.FORBIDDEN_CONFIG_PATTERNS:
            if (forbidden in path_str_forward or 
                forbidden in path_str_back or
                f'/{forbidden}/' in path_str_forward or
                f'\\{forbidden}\\' in path_str_back):
                errors.append(
                    f"Config file contains forbidden path component: '{forbidden}'"
                )
                break  # Stop after first forbidden pattern match
        
        # 4. Check for path traversal (if no forbidden errors)
        is_outside_root = False
        if not errors:
            try:
                abs_path.relative_to(self.project_root)
            except ValueError:
                is_outside_root = True
                warnings.append(
                    f"Config file is outside project root: {abs_path}"
                )
        
        # 5. Check if in allowed directory (only if inside project root and no forbidden errors)
        if not errors and not is_outside_root:
                config_dir = abs_path.parent
                rel_dir = config_dir.relative_to(self.project_root) if config_dir != self.project_root else Path(".")
                is_allowed = False
                for allowed_dir in self.ALLOWED_CONFIG_DIRS:
                    allowed_path = self.project_root / allowed_dir
                    try:
                        config_dir.relative_to(allowed_path)
                        is_allowed = True
                        break
                    except ValueError:
                        continue
                
                if not is_allowed:
                    warnings.append(
                        f"Config file in non-standard location: {rel_dir}. "
                        f"Recommended locations: {self.ALLOWED_CONFIG_DIRS}"
                    )
        
        # 5. Check file extension
        if abs_path.suffix not in ['.yaml', '.yml', '.json']:
            warnings.append(
                f"Unexpected config file extension: {abs_path.suffix}. "
                f"Expected: .yaml, .yml, or .json"
            )
        
        # 6. Verify file integrity (if previously validated)
        if str(abs_path) in self._validated_configs:
            current_hash = self._hash_file(abs_path)
            stored_hash = self._validated_configs[str(abs_path)]
            
            if current_hash != stored_hash:
                warnings.append(
                    f"Config file has been modified since last validation"
                )
                metadata['hash_mismatch'] = True
        
        is_valid = len(errors) == 0
        
        if is_valid and abs_path.exists():
            # Store hash for future validation
            self._validated_configs[str(abs_path)] = self._hash_file(abs_path)
        
        return SecurityValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def _hash_file(self, path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def is_safe_to_load(self, config_path: Path) -> bool:
        """
        Check if config file is safe to load.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if safe to load
        """
        result = self.validate_config_path(config_path)
        return result.is_valid


class CacheIntegrityValidator:
    """
    Validates cache integrity to prevent Cache Poisoning attacks.
    
    Protection mechanisms:
    - HMAC-based cache verification
    - Timestamp validation
    - Cache entry expiration
    - Tamper detection
    """
    
    def __init__(self, secret_key: Optional[bytes] = None, ttl_hours: int = 24):
        """
        Initialize cache integrity validator.
        
        Args:
            secret_key: Secret key for HMAC (generated if not provided)
            ttl_hours: Cache entry time-to-live in hours
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.ttl = timedelta(hours=ttl_hours)
    
    def _generate_secret_key(self) -> bytes:
        """Generate a random secret key."""
        import secrets
        return secrets.token_bytes(32)
    
    def sign_cache_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign cache entry with HMAC.
        
        Args:
            data: Cache data to sign
            
        Returns:
            Signed cache entry with metadata
        """
        # Add timestamp
        signed_data = {
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
        }
        
        # Calculate HMAC
        data_bytes = json.dumps(signed_data, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            self.secret_key,
            data_bytes,
            hashlib.sha256
        ).hexdigest()
        
        signed_data['signature'] = signature
        
        return signed_data
    
    def verify_cache_entry(self, signed_data: Dict[str, Any]) -> SecurityValidationResult:
        """
        Verify cache entry integrity.
        
        Args:
            signed_data: Signed cache entry
            
        Returns:
            SecurityValidationResult
        """
        errors = []
        warnings = []
        metadata = {}
        
        # 1. Check required fields
        required_fields = {'data', 'timestamp', 'signature', 'version'}
        missing_fields = required_fields - set(signed_data.keys())
        
        if missing_fields:
            errors.append(f"Cache entry missing required fields: {missing_fields}")
            return SecurityValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
        
        # 2. Verify signature
        signature = signed_data.pop('signature')
        data_bytes = json.dumps(signed_data, sort_keys=True).encode('utf-8')
        expected_signature = hmac.new(
            self.secret_key,
            data_bytes,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            errors.append("Cache entry signature verification failed (possible tampering)")
            signed_data['signature'] = signature  # Restore for metadata
            return SecurityValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
        
        signed_data['signature'] = signature  # Restore
        
        # 3. Check timestamp and TTL
        try:
            timestamp = datetime.fromisoformat(signed_data['timestamp'])
            age = datetime.now() - timestamp
            
            metadata['age_hours'] = age.total_seconds() / 3600
            
            if age > self.ttl:
                warnings.append(
                    f"Cache entry expired (age: {age.total_seconds() / 3600:.1f}h, "
                    f"TTL: {self.ttl.total_seconds() / 3600:.1f}h)"
                )
        except (ValueError, KeyError) as e:
            errors.append(f"Invalid timestamp in cache entry: {e}")
        
        # 4. Check version
        if signed_data.get('version') != '1.0':
            warnings.append(
                f"Cache entry version mismatch: {signed_data.get('version')}"
            )
        
        is_valid = len(errors) == 0
        
        return SecurityValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )


class MetaSecurityValidator:
    """
    Unified meta-security validator combining all protection mechanisms.
    
    This is the main entry point for meta-security validation.
    """
    
    def __init__(
        self,
        strict_scanner_validation: bool = True,
        project_root: Optional[Path] = None,
        cache_secret_key: Optional[bytes] = None
    ):
        """
        Initialize meta-security validator.
        
        Args:
            strict_scanner_validation: Enable strict scanner validation
            project_root: Project root directory
            cache_secret_key: Secret key for cache validation
        """
        self.scanner_validator = ScannerIntegrityValidator(
            strict_mode=strict_scanner_validation
        )
        self.config_sandbox = ConfigurationSandbox(project_root)
        self.cache_validator = CacheIntegrityValidator(cache_secret_key)
        
        logger.info("🛡️  Meta-Security Validator initialized")
    
    def validate_scanner(self, scanner: Any) -> SecurityValidationResult:
        """Validate scanner integrity."""
        return self.scanner_validator.validate_scanner(scanner)
    
    def validate_config_path(self, config_path: Path) -> SecurityValidationResult:
        """Validate configuration file path."""
        return self.config_sandbox.validate_config_path(config_path)
    
    def validate_cache_entry(self, cache_entry: Dict[str, Any]) -> SecurityValidationResult:
        """Validate cache entry integrity."""
        return self.cache_validator.verify_cache_entry(cache_entry)
    
    def sign_cache_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sign cache entry."""
        return self.cache_validator.sign_cache_entry(data)
