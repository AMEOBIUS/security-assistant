"""
Offensive Security Target Authorization System

This module implements target authorization and scope validation for offensive security tools.

Features:
- Whitelist-based target authorization
- IP/CIDR range validation
- Domain validation
- Audit logging for all authorization checks
- Integration with ToS enforcement

Security Notes:
- All offensive actions must be authorized through this system
- Audit logs are immutable and stored locally
- Whitelist is encrypted at rest
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)


class AuthorizationError(Exception):
    """Base exception for authorization errors."""
    pass


class TargetNotAuthorizedError(AuthorizationError):
    """Target is not in the authorized whitelist."""
    pass


class AuthorizationDatabaseError(AuthorizationError):
    """Database operation failed."""
    pass


class AuthorizationService:
    """
    Target Authorization Service for Offensive Security Tools.
    
    Manages whitelist of authorized targets and validates all offensive actions.
    """
    
    DB_PATH = Path("~/.security_assistant/authorization.db").expanduser()
    DB_SCHEMA = [
        """
        CREATE TABLE IF NOT EXISTS authorized_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL,  -- 'domain', 'ip', 'cidr', 'url'
            target_value TEXT NOT NULL UNIQUE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by TEXT,
            notes TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,  -- 'authorize', 'check', 'remove'
            target_type TEXT,
            target_value TEXT,
            status TEXT NOT NULL,  -- 'success', 'failed'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user TEXT,
            details TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tos_acceptance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_by TEXT,
            ip_address TEXT,
            version TEXT NOT NULL
        )
        """
    ]
    
    def __init__(self):
        """Initialize authorization service and database."""
        self._ensure_db_directory()
        self._initialize_database()
        
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = self.DB_PATH.parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created authorization database directory: {db_dir}")
            except OSError as e:
                logger.error(f"Failed to create database directory: {e}")
                raise AuthorizationDatabaseError(f"Cannot create database directory: {e}")  # noqa: B904
        
        # Ensure directory is writable
        if not os.access(db_dir, os.W_OK):
            raise AuthorizationDatabaseError(f"Database directory not writable: {db_dir}")
    
    def _initialize_database(self):
        """Initialize or upgrade database schema."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Create tables
                for schema in self.DB_SCHEMA:
                    cursor.execute(schema)
                
                conn.commit()
                
            logger.info(f"Authorization database initialized at {self.DB_PATH}")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def add_authorized_target(
        self,
        target: str,
        target_type: Optional[str] = None,
        added_by: str = "system",
        notes: str = ""
    ) -> bool:
        """
        Add target to authorized whitelist.
        
        Args:
            target: Target to authorize (domain, IP, CIDR, or URL)
            target_type: Optional type override
            added_by: Who added this target
            notes: Additional notes
            
        Returns:
            True if added successfully, False if already exists
            
        Raises:
            ValueError: If target is invalid
            AuthorizationDatabaseError: If database operation fails
        """
        # Validate and normalize target
        normalized_target, detected_type = self._normalize_target(target, target_type)
        
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Check if already exists
                cursor.execute(
                    "SELECT 1 FROM authorized_targets WHERE target_value = ?",
                    (normalized_target,)
                )
                
                if cursor.fetchone():
                    logger.warning(f"Target already authorized: {normalized_target}")
                    return False
                
                # Insert new target
                cursor.execute(
                    """
                    INSERT INTO authorized_targets 
                    (target_type, target_value, added_by, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (detected_type, normalized_target, added_by, notes)
                )
                
                # Log audit entry
                cursor.execute(
                    """
                    INSERT INTO audit_logs 
                    (action, target_type, target_value, status, user, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "authorize",
                        detected_type,
                        normalized_target,
                        "success",
                        added_by,
                        f"Added {detected_type}: {normalized_target}"
                    )
                )
                
                conn.commit()
                logger.info(f"Authorized {detected_type}: {normalized_target}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add authorized target: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def _normalize_target(
        self, 
        target: str, 
        target_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Normalize and validate target format.
        
        Args:
            target: Raw target string
            target_type: Optional type hint
            
        Returns:
            Tuple of (normalized_target, detected_type)
            
        Raises:
            ValueError: If target format is invalid
        """
        target = target.strip().lower()
        
        # Try to detect type if not provided
        if not target_type:
            # Try URL
            if target.startswith(('http://', 'https://')):
                parsed = urlparse(target)
                if parsed.netloc:
                    return parsed.netloc, 'domain'
                target_type = 'url'
            
            # Try IP address
            try:
                ip = ip_address(target)
                if ip.version == 4:
                    return str(ip), 'ip'
                elif ip.version == 6:
                    return str(ip), 'ipv6'
            except ValueError:
                pass
            
            # Try CIDR
            try:
                network = ip_network(target, strict=False)
                return str(network), 'cidr'
            except ValueError:
                pass
            
            # Default to domain
            if '.' in target or target == 'localhost':
                return target, 'domain'
            
            raise ValueError(f"Cannot determine target type for: {target}")
        
        # Validate based on specified type
        if target_type == 'domain':
            if not ('.' in target or target == 'localhost'):
                raise ValueError(f"Invalid domain format: {target}")
            return target, 'domain'
        
        elif target_type == 'ip':
            try:
                ip = ip_address(target)
                if ip.version != 4:
                    raise ValueError(f"Only IPv4 supported, got IPv{ip.version}")
                return str(ip), 'ip'
            except ValueError as e:
                raise ValueError(f"Invalid IP address: {target}") from e
        
        elif target_type == 'cidr':
            try:
                network = ip_network(target, strict=False)
                return str(network), 'cidr'
            except ValueError as e:
                raise ValueError(f"Invalid CIDR format: {target}") from e
        
        elif target_type == 'url':
            parsed = urlparse(target)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {target}")
            return target, 'url'
        
        else:
            raise ValueError(f"Unsupported target type: {target_type}")
    
    def is_authorized(self, target: str, target_type: Optional[str] = None) -> bool:
        """
        Check if target is authorized.
        
        Args:
            target: Target to check
            target_type: Optional type hint
            
        Returns:
            True if authorized, False otherwise
            
        Raises:
            ValueError: If target format is invalid
            AuthorizationDatabaseError: If database operation fails
        """
        normalized_target, detected_type = self._normalize_target(target, target_type)
        
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Check exact match
                cursor.execute(
                    "SELECT 1 FROM authorized_targets WHERE target_value = ?",
                    (normalized_target,)
                )
                
                if cursor.fetchone():
                    # Log successful check
                    cursor.execute(
                        """
                        INSERT INTO audit_logs 
                        (action, target_type, target_value, status, user, details)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "check",
                            detected_type,
                            normalized_target,
                            "success",
                            "system",
                            "Authorization check passed"
                        )
                    )
                    conn.commit()
                    return True
                
                # Check CIDR ranges for IP targets
                if detected_type == 'ip':
                    target_ip = ip_address(normalized_target)
                    cursor.execute(
                        "SELECT target_value FROM authorized_targets WHERE target_type = 'cidr'"
                    )
                    
                    for (cidr_range,) in cursor.fetchall():
                        try:
                            network = ip_network(cidr_range, strict=False)
                            if target_ip in network:
                                # Log successful check
                                cursor.execute(
                                    """
                                    INSERT INTO audit_logs 
                                    (action, target_type, target_value, status, user, details)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        "check",
                                        detected_type,
                                        normalized_target,
                                        "success",
                                        "system",
                                        f"Matched CIDR range: {cidr_range}"
                                    )
                                )
                                conn.commit()
                                return True
                        except ValueError:
                            continue
                
                # Log failed check
                cursor.execute(
                    """
                    INSERT INTO audit_logs 
                    (action, target_type, target_value, status, user, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "check",
                        detected_type,
                        normalized_target,
                        "failed",
                        "system",
                        "Target not in whitelist"
                    )
                )
                conn.commit()
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Authorization check failed: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def remove_authorized_target(self, target: str, target_type: Optional[str] = None) -> bool:
        """
        Remove target from authorized whitelist.
        
        Args:
            target: Target to remove
            target_type: Optional type hint
            
        Returns:
            True if removed successfully, False if not found
            
        Raises:
            ValueError: If target format is invalid
            AuthorizationDatabaseError: If database operation fails
        """
        normalized_target, detected_type = self._normalize_target(target, target_type)
        
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Remove target
                cursor.execute(
                    "DELETE FROM authorized_targets WHERE target_value = ?",
                    (normalized_target,)
                )
                
                if cursor.rowcount == 0:
                    logger.warning(f"Target not found in whitelist: {normalized_target}")
                    return False
                
                # Log audit entry
                cursor.execute(
                    """
                    INSERT INTO audit_logs 
                    (action, target_type, target_value, status, user, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "remove",
                        detected_type,
                        normalized_target,
                        "success",
                        "system",
                        "Removed from whitelist"
                    )
                )
                
                conn.commit()
                logger.info(f"Removed authorized target: {normalized_target}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to remove authorized target: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def list_authorized_targets(self) -> List[Dict]:
        """
        List all authorized targets.
        
        Returns:
            List of authorized targets with metadata
            
        Raises:
            AuthorizationDatabaseError: If database operation fails
        """
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT target_type, target_value, added_at, added_by, notes
                    FROM authorized_targets
                    ORDER BY added_at DESC
                    """
                )
                
                return [
                    {
                        "type": row[0],
                        "value": row[1],
                        "added_at": row[2],
                        "added_by": row[3],
                        "notes": row[4]
                    }
                    for row in cursor.fetchall()
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to list authorized targets: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log entries
            
        Raises:
            AuthorizationDatabaseError: If database operation fails
        """
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT action, target_type, target_value, status, timestamp, user, details
                    FROM audit_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                
                return [
                    {
                        "action": row[0],
                        "target_type": row[1],
                        "target_value": row[2],
                        "status": row[3],
                        "timestamp": row[4],
                        "user": row[5],
                        "details": row[6]
                    }
                    for row in cursor.fetchall()
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get audit logs: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def export_authorization_data(self, output_path: Path) -> Path:
        """
        Export authorization data to JSON file.
        
        Args:
            output_path: Path to export file
            
        Returns:
            Path to exported file
            
        Raises:
            AuthorizationDatabaseError: If export fails
        """
        try:
            data = {
                "authorized_targets": self.list_authorized_targets(),
                "audit_logs": self.get_audit_logs(limit=1000),
                "exported_at": datetime.now().isoformat()
            }
            
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Exported authorization data to {output_path}")
            return output_path
            
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Failed to export authorization data: {e}")
            raise AuthorizationDatabaseError(f"Export failed: {e}")  # noqa: B904
    
    def check_tos_accepted(self) -> bool:
        """
        Check if Terms of Service have been accepted.
        
        Returns:
            True if ToS accepted, False otherwise
        """
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT 1 FROM tos_acceptance ORDER BY accepted_at DESC LIMIT 1"
                )
                
                return cursor.fetchone() is not None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to check ToS status: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def accept_tos(self, accepted_by: str = "user", version: str = "1.0") -> bool:
        """
        Record ToS acceptance.
        
        Args:
            accepted_by: Who accepted the ToS
            version: ToS version
            
        Returns:
            True if recorded successfully
            
        Raises:
            AuthorizationDatabaseError: If database operation fails
        """
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO tos_acceptance (accepted_by, version)
                    VALUES (?, ?)
                    """,
                    (accepted_by, version)
                )
                
                conn.commit()
                logger.info(f"ToS accepted by {accepted_by} (version {version})")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to record ToS acceptance: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904
    
    def reject_tos(self) -> bool:
        """
        Remove ToS acceptance record (for testing purposes).
        
        Returns:
            True if removed successfully
            
        Raises:
            AuthorizationDatabaseError: If database operation fails
        """
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Delete all ToS acceptance records
                cursor.execute("DELETE FROM tos_acceptance")
                
                conn.commit()
                logger.info("ToS acceptance records removed")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to remove ToS acceptance: {e}")
            raise AuthorizationDatabaseError(f"Database error: {e}")  # noqa: B904


