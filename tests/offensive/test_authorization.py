"""
Unit tests for offensive security authorization system.
"""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from security_assistant.offensive.authorization import (
    AuthorizationDatabaseError,
    AuthorizationService,
    TargetNotAuthorizedError,
)


class TestAuthorizationService:
    """Test AuthorizationService class."""
    
    def setup_method(self):
        """Setup test database."""
        # Use temporary database for tests
        self.temp_db = Path(tempfile.gettempdir()) / "test_auth.db"
        
        # Clean up any leftover database and WAL files from previous test
        import gc
        import time
        gc.collect()  # Release any lingering connections
        
        for db_file in [self.temp_db, 
                        self.temp_db.with_suffix('.db-wal'),
                        self.temp_db.with_suffix('.db-shm')]:
            if db_file.exists():
                for _ in range(5):
                    try:
                        db_file.unlink()
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.1)
        
        # Mock database path
        self.original_db_path = AuthorizationService.DB_PATH
        AuthorizationService.DB_PATH = self.temp_db
        
        # Initialize service
        self.service = AuthorizationService()
        
    def teardown_method(self):
        """Cleanup test database."""
        import gc
        import time
        
        # Force garbage collection to release SQLite connections
        self.service = None
        gc.collect()
        
        # Restore original path
        AuthorizationService.DB_PATH = self.original_db_path
        
        # Remove temp database and WAL files with retry
        for db_file in [self.temp_db, 
                        self.temp_db.with_suffix('.db-wal'),
                        self.temp_db.with_suffix('.db-shm')]:
            if db_file.exists():
                for _ in range(5):
                    try:
                        db_file.unlink()
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.1)
    
    def test_initialization(self):
        """Test service initialization."""
        assert self.service is not None
        assert self.temp_db.exists()
    
    def test_add_domain_target(self):
        """Test adding domain target."""
        result = self.service.add_authorized_target("example.com")
        assert result is True
        
        # Should not add duplicate
        result = self.service.add_authorized_target("example.com")
        assert result is False
    
    def test_add_ip_target(self):
        """Test adding IP target."""
        result = self.service.add_authorized_target("192.168.1.1")
        assert result is True
    
    def test_add_cidr_target(self):
        """Test adding CIDR target."""
        result = self.service.add_authorized_target("192.168.1.0/24")
        assert result is True
    
    def test_add_url_target(self):
        """Test adding URL target."""
        result = self.service.add_authorized_target("https://example.com")
        assert result is True
    
    def test_invalid_target(self):
        """Test invalid target format."""
        with pytest.raises(ValueError):
            self.service.add_authorized_target("invalid-target")
    
    def test_is_authorized_exact_match(self):
        """Test exact target authorization check."""
        # Add target
        self.service.add_authorized_target("example.com")
        
        # Check authorization
        result = self.service.is_authorized("example.com")
        assert result is True
    
    def test_is_authorized_ip_in_cidr(self):
        """Test IP in CIDR range authorization."""
        # Add CIDR range
        self.service.add_authorized_target("192.168.1.0/24")
        
        # Check IP in range
        result = self.service.is_authorized("192.168.1.100")
        assert result is True
    
    def test_is_authorized_not_in_whitelist(self):
        """Test unauthorized target."""
        result = self.service.is_authorized("unauthorized.com")
        assert result is False
    
    def test_remove_authorized_target(self):
        """Test removing authorized target."""
        # Add target
        self.service.add_authorized_target("example.com")
        
        # Remove target
        result = self.service.remove_authorized_target("example.com")
        assert result is True
        
        # Check it's removed
        result = self.service.is_authorized("example.com")
        assert result is False
    
    def test_list_authorized_targets(self):
        """Test listing authorized targets."""
        # Add targets
        self.service.add_authorized_target("example.com")
        self.service.add_authorized_target("192.168.1.1")
        
        # List targets
        targets = self.service.list_authorized_targets()
        assert len(targets) == 2
        assert targets[0]["value"] in ["example.com", "192.168.1.1"]
    
    def test_get_audit_logs(self):
        """Test getting audit logs."""
        # Add target (creates audit log)
        self.service.add_authorized_target("example.com")
        
        # Get logs
        logs = self.service.get_audit_logs(limit=10)
        assert len(logs) >= 1
        assert logs[0]["action"] == "authorize"
    
    def test_tos_acceptance(self):
        """Test ToS acceptance."""
        # Initially not accepted
        result = self.service.check_tos_accepted()
        assert result is False
        
        # Accept ToS
        result = self.service.accept_tos("test-user", "1.0")
        assert result is True
        
        # Check accepted
        result = self.service.check_tos_accepted()
        assert result is True
    
    def test_export_data(self):
        """Test exporting authorization data."""
        # Add target
        self.service.add_authorized_target("example.com")
        
        # Export
        output_path = Path(tempfile.gettempdir()) / "export.json"
        result = self.service.export_authorization_data(output_path)
        
        assert result.exists()
        
        # Verify content
        with output_path.open('r') as f:
            data = json.load(f)
            assert "authorized_targets" in data
            assert len(data["authorized_targets"]) >= 1


class TestAuthorizationErrors:
    """Test authorization error handling."""
    
    def setup_method(self):
        """Setup test database."""
        import gc
        import time
        gc.collect()  # Release any lingering connections
        
        self.temp_db = Path(tempfile.gettempdir()) / "test_auth_errors.db"
        
        # Clean up any leftover database and WAL files from previous test
        for db_file in [self.temp_db, 
                        self.temp_db.with_suffix('.db-wal'),
                        self.temp_db.with_suffix('.db-shm')]:
            if db_file.exists():
                for _ in range(5):
                    try:
                        db_file.unlink()
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.1)
        
        self.original_db_path = AuthorizationService.DB_PATH
        AuthorizationService.DB_PATH = self.temp_db
        
        self.service = AuthorizationService()
    
    def teardown_method(self):
        """Cleanup test database."""
        import gc
        import time
        
        # Force garbage collection to release SQLite connections
        self.service = None
        gc.collect()
        
        AuthorizationService.DB_PATH = self.original_db_path
        
        # Remove temp database and WAL files with retry
        for db_file in [self.temp_db, 
                        self.temp_db.with_suffix('.db-wal'),
                        self.temp_db.with_suffix('.db-shm')]:
            if db_file.exists():
                for _ in range(5):
                    try:
                        db_file.unlink()
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.1)
    
    def test_database_error_on_init(self):
        """Test database error during initialization."""
        import time
        # Use a separate file for corruption test
        corrupted_db = Path(tempfile.gettempdir()) / "test_auth_corrupted.db"
        
        try:
            # Write corrupted data
            with corrupted_db.open('w') as f:
                f.write("corrupted data")
            
            # Temporarily change DB_PATH to corrupted file
            old_path = AuthorizationService.DB_PATH
            AuthorizationService.DB_PATH = corrupted_db
            
            try:
                with pytest.raises(AuthorizationDatabaseError):
                    AuthorizationService()
            finally:
                AuthorizationService.DB_PATH = old_path
        finally:
            # Clean up corrupted file
            if corrupted_db.exists():
                for _ in range(5):
                    try:
                        corrupted_db.unlink()
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.1)
    
    def test_database_error_on_add(self):
        """Test database error during add operation."""
        # Mock database error
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Mock error")
            
            with pytest.raises(AuthorizationDatabaseError):
                self.service.add_authorized_target("example.com")
    
    def test_target_not_authorized_error(self):
        """Test TargetNotAuthorizedError - is_authorized returns False for unauthorized targets."""
        # is_authorized returns False for unauthorized targets, doesn't raise
        result = self.service.is_authorized("unauthorized.com")
        assert result is False
        
        # TargetNotAuthorizedError is raised by other methods that require authorization
        # Testing that it can be instantiated
        error = TargetNotAuthorizedError("Test target")
        assert str(error) == "Test target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
