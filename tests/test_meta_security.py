"""
Tests for Meta-Security Validation

Tests the security validator that prevents meta-attacks on the
security workstation itself.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from security_assistant.scanners.bandit_scanner import BanditScanner
from security_assistant.scanners.semgrep_scanner import SemgrepScanner
from security_assistant.scanners.trivy_scanner import TrivyScanner
from security_assistant.security_validator import (
    CacheIntegrityValidator,
    ConfigurationSandbox,
    MetaSecurityValidator,
    ScannerIntegrityValidator,
)


class TestScannerIntegrityValidator:
    """Test scanner integrity validation."""
    
    def test_valid_bandit_scanner(self):
        """Test validation of legitimate Bandit scanner."""
        validator = ScannerIntegrityValidator(strict_mode=True)
        scanner = BanditScanner()
        
        result = validator.validate_scanner(scanner)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert validator.is_validated(scanner)
    
    @patch('subprocess.run')
    def test_valid_semgrep_scanner(self, mock_run):
        """Test validation of legitimate Semgrep scanner."""
        # Skip if semgrep module not installed
        try:
            import semgrep  # noqa: F401
        except ImportError:
            pytest.skip("Semgrep not installed")
        
        # Mock semgrep CLI availability
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"version": "1.23.0"}',
            stderr=""
        )
        
        validator = ScannerIntegrityValidator(strict_mode=True)
        scanner = SemgrepScanner()
        
        result = validator.validate_scanner(scanner)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_trivy_scanner(self):
        """Test validation of legitimate Trivy scanner."""
        validator = ScannerIntegrityValidator(strict_mode=True)
        try:
            scanner = TrivyScanner()
        except Exception:
            pytest.skip("Trivy not installed")
        
        result = validator.validate_scanner(scanner)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_malicious_scanner_rejected(self):
        """Test that malicious scanner is rejected."""
        validator = ScannerIntegrityValidator(strict_mode=True)
        
        # Create fake malicious scanner
        class MaliciousScanner:
            def scan_directory(self, directory):
                pass
            
            def scan_file(self, file_path):
                pass
            
            def exec(self, code):
                """Malicious method"""
                pass
        
        scanner = MaliciousScanner()
        result = validator.validate_scanner(scanner)
        
        # Should fail in strict mode (not in whitelist)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "not in whitelist" in result.errors[0]
    
    def test_scanner_missing_methods(self):
        """Test scanner with missing required methods."""
        validator = ScannerIntegrityValidator(strict_mode=False)
        
        class IncompleteScanner:
            def scan_directory(self, directory):
                pass
            # Missing scan_file method
        
        scanner = IncompleteScanner()
        result = validator.validate_scanner(scanner)
        
        assert not result.is_valid
        assert any("missing required methods" in err for err in result.errors)
    
    def test_non_strict_mode(self):
        """Test non-strict mode allows custom scanners."""
        validator = ScannerIntegrityValidator(strict_mode=False)
        
        class CustomScanner:
            def scan_directory(self, directory):
                return []
            
            def scan_file(self, file_path):
                return []
        
        scanner = CustomScanner()
        result = validator.validate_scanner(scanner)
        
        # Should pass in non-strict mode if has required methods
        assert result.is_valid


class TestConfigurationSandbox:
    """Test configuration sandboxing."""
    
    def test_valid_config_in_project_root(self):
        """Test valid config file in project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_file = project_root / "security-assistant.yaml"
            config_file.write_text("test: config")
            
            sandbox = ConfigurationSandbox(project_root)
            result = sandbox.validate_config_path(config_file)
            
            assert result.is_valid
            assert len(result.errors) == 0
    
    def test_valid_config_in_config_dir(self):
        """Test valid config file in .config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_dir = project_root / ".config"
            config_dir.mkdir()
            config_file = config_dir / "security-assistant.yaml"
            config_file.write_text("test: config")
            
            sandbox = ConfigurationSandbox(project_root)
            result = sandbox.validate_config_path(config_file)
            
            assert result.is_valid
            assert len(result.errors) == 0
    
    def test_config_in_forbidden_location(self):
        """Test config file in forbidden location (.git)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            git_dir = project_root / ".git"
            git_dir.mkdir()
            config_file = git_dir / "config.yaml"
            config_file.write_text("test: config")
            
            sandbox = ConfigurationSandbox(project_root)
            result = sandbox.validate_config_path(config_file)
            
            assert not result.is_valid
            assert any(".git" in err for err in result.errors)
    
    def test_config_outside_project_root(self):
        """Test config file outside project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            
            # Config outside project
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("test: config")
            
            sandbox = ConfigurationSandbox(project_root)
            result = sandbox.validate_config_path(config_file)
            
            # Should have warning about being outside project root
            assert any("outside project root" in warn for warn in result.warnings)
    
    def test_nonexistent_config_file(self):
        """Test nonexistent config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_file = project_root / "nonexistent.yaml"
            
            sandbox = ConfigurationSandbox(project_root)
            result = sandbox.validate_config_path(config_file)
            
            assert not result.is_valid
            assert any("does not exist" in err for err in result.errors)
    
    def test_config_file_integrity_check(self):
        """Test config file integrity verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_file = project_root / "config.yaml"
            config_file.write_text("test: config")
            
            sandbox = ConfigurationSandbox(project_root)
            
            # First validation
            result1 = sandbox.validate_config_path(config_file)
            assert result1.is_valid
            
            # Modify file
            config_file.write_text("test: modified")
            
            # Second validation should detect modification
            result2 = sandbox.validate_config_path(config_file)
            assert result2.is_valid  # Still valid, but has warning
            assert any("modified" in warn for warn in result2.warnings)


class TestCacheIntegrityValidator:
    """Test cache integrity validation."""
    
    def test_sign_and_verify_cache_entry(self):
        """Test signing and verifying cache entry."""
        validator = CacheIntegrityValidator()
        
        data = {
            'findings': [
                {'severity': 'HIGH', 'file': 'test.py'}
            ],
            'scan_time': '2025-12-01T10:00:00'
        }
        
        # Sign entry
        signed = validator.sign_cache_entry(data)
        
        assert 'signature' in signed
        assert 'timestamp' in signed
        assert 'data' in signed
        
        # Verify entry
        result = validator.verify_cache_entry(signed)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_tampered_cache_entry_rejected(self):
        """Test that tampered cache entry is rejected."""
        validator = CacheIntegrityValidator()
        
        data = {'findings': []}
        signed = validator.sign_cache_entry(data)
        
        # Tamper with data
        signed['data']['findings'] = [{'severity': 'CRITICAL'}]
        
        # Verification should fail
        result = validator.verify_cache_entry(signed)
        
        assert not result.is_valid
        assert any("signature verification failed" in err for err in result.errors)
    
    def test_expired_cache_entry(self):
        """Test expired cache entry detection."""
        validator = CacheIntegrityValidator(ttl_hours=1)
        
        data = {'findings': []}
        signed = validator.sign_cache_entry(data)
        
        # Manually set old timestamp
        old_time = datetime.now() - timedelta(hours=2)
        signed['timestamp'] = old_time.isoformat()
        
        # Recalculate signature with old timestamp
        import hashlib
        import hmac
        signature = signed.pop('signature')
        data_bytes = json.dumps(signed, sort_keys=True).encode('utf-8')
        new_signature = hmac.new(
            validator.secret_key,
            data_bytes,
            hashlib.sha256
        ).hexdigest()
        signed['signature'] = new_signature
        
        # Verify - should have warning about expiration
        result = validator.verify_cache_entry(signed)
        
        assert result.is_valid  # Valid signature
        assert any("expired" in warn for warn in result.warnings)
    
    def test_missing_signature_rejected(self):
        """Test cache entry without signature is rejected."""
        validator = CacheIntegrityValidator()
        
        # Entry without signature
        entry = {
            'data': {'findings': []},
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        result = validator.verify_cache_entry(entry)
        
        assert not result.is_valid
        assert any("missing required fields" in err for err in result.errors)


class TestMetaSecurityValidator:
    """Test unified meta-security validator."""
    
    def test_validate_legitimate_scanner(self):
        """Test validation of legitimate scanner."""
        validator = MetaSecurityValidator()
        scanner = BanditScanner()
        
        result = validator.validate_scanner(scanner)
        
        assert result.is_valid
    
    def test_validate_config_path(self):
        """Test config path validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_file = project_root / "config.yaml"
            config_file.write_text("test: config")
            
            validator = MetaSecurityValidator(project_root=project_root)
            result = validator.validate_config_path(config_file)
            
            assert result.is_valid
    
    def test_sign_and_verify_cache(self):
        """Test cache signing and verification."""
        validator = MetaSecurityValidator()
        
        data = {'findings': []}
        signed = validator.sign_cache_entry(data)
        result = validator.validate_cache_entry(signed)
        
        assert result.is_valid


class TestOrchestratorIntegration:
    """Test meta-security integration with orchestrator."""
    
    def test_orchestrator_validates_scanners(self):
        """Test that orchestrator validates scanners when enabled."""
        from security_assistant.orchestrator import ScannerType, ScanOrchestrator
        
        orchestrator = ScanOrchestrator(enable_meta_security=True)
        
        # Should successfully enable legitimate scanner
        orchestrator.enable_scanner(ScannerType.BANDIT)
        
        assert ScannerType.BANDIT in orchestrator._enabled_scanners
    
    def test_orchestrator_rejects_invalid_scanner(self):
        """Test that orchestrator rejects invalid scanners."""
        from security_assistant.orchestrator import ScannerType, ScanOrchestrator
        
        orchestrator = ScanOrchestrator(enable_meta_security=True)
        
        # Create fake scanner
        class FakeScanner:
            def scan_directory(self, directory):
                pass
            def scan_file(self, file_path):
                pass
        
        # Should raise ValueError due to validation failure
        with pytest.raises(ValueError, match="Scanner validation failed"):
            orchestrator.enable_scanner(
                ScannerType.BANDIT,
                scanner_instance=FakeScanner()
            )
    
    def test_orchestrator_without_meta_security(self):
        """Test orchestrator with meta-security disabled."""
        from security_assistant.orchestrator import ScannerType, ScanOrchestrator
        
        orchestrator = ScanOrchestrator(enable_meta_security=False)
        
        # Should work without validation
        orchestrator.enable_scanner(ScannerType.BANDIT)
        
        assert ScannerType.BANDIT in orchestrator._enabled_scanners


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
