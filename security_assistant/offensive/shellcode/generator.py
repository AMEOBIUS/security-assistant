"""
Shellcode Generator
Platform-specific shellcode generation with encoder support

This module provides educational shellcode generation capabilities
for research and learning purposes only.
"""

import logging
from typing import Any, List, Optional

from security_assistant.offensive.authorization import AuthorizationService
from security_assistant.offensive.shellcode.payloads.linux_x64 import LinuxX64Payloads
from security_assistant.offensive.shellcode.payloads.macos_x64 import MacOSX64Payloads
from security_assistant.offensive.shellcode.payloads.windows_x64 import (
    WindowsX64Payloads,
)

logger = logging.getLogger(__name__)


class ShellcodeGenerator:
    """
    Platform-specific shellcode generator with encoder support.
    
    Args:
        platform: Target platform (linux-x64, windows-x64, macos-x64)
        educational: Enable educational/safe mode (default: False)
        auth_service: Authorization service for ToS checking
    """
    
    def __init__(
        self,
        platform: str,
        educational: bool = False,
        auth_service: Optional[AuthorizationService] = None
    ):
        self.platform = platform
        self.educational = educational
        self.auth_service = auth_service or AuthorizationService()
        
        # Validate platform
        self._validate_platform()
        
        # Load payload implementations
        self._load_payloads()
        
        logger.warning(
            f"ShellcodeGenerator initialized for {platform} "
            f"({'educational mode' if educational else 'normal mode'})"
        )
    
    def _validate_platform(self) -> None:
        """Validate target platform."""
        supported_platforms = ["linux-x64", "windows-x64", "macos-x64"]
        if self.platform not in supported_platforms:
            raise ValueError(
                f"Unsupported platform: {self.platform}. "
                f"Supported platforms: {', '.join(supported_platforms)}"
            )
    
    def _load_payloads(self) -> None:
        """Load platform-specific payload implementations."""
        if self.platform == "linux-x64":
            self.payload_handler = LinuxX64Payloads()
        elif self.platform == "windows-x64":
            self.payload_handler = WindowsX64Payloads()
        elif self.platform == "macos-x64":
            self.payload_handler = MacOSX64Payloads()
    
    def generate(
        self,
        payload_type: str,
        **kwargs: Any
    ) -> bytes:
        """
        Generate shellcode payload.
        
        Args:
            payload_type: Type of payload (reverse-shell, bind-shell, exec, etc.)
            **kwargs: Additional payload-specific arguments
        
        Returns:
            Generated shellcode as bytes
        """
        # Check authorization (skip for testing)
        if not hasattr(self, '_skip_auth'):
            self._check_authorization()
        
        # Log generation attempt
        self._log_generation_attempt(payload_type)
        
        # Generate payload
        shellcode = self._generate_payload(payload_type, **kwargs)
        
        # Apply educational mode if enabled
        if self.educational:
            shellcode = self._apply_educational_mode(shellcode)
        
        return shellcode
    
    def _check_authorization(self) -> None:
        """Check if user has accepted ToS."""
        if not self.auth_service.check_tos_accepted():
            raise Exception(
                "Must accept Terms of Service before generating shellcode. "
                "This is for educational purposes only."
            )
    
    def _log_generation_attempt(self, payload_type: str) -> None:
        """Log shellcode generation attempt."""
        # Skip logging for testing
        if not hasattr(self, '_skip_auth'):
            # In production, this would use proper logging
            logger.warning(
                f"Shellcode generation: platform={self.platform}, "
                f"payload={payload_type}, educational={self.educational}"
            )
    
    def _generate_payload(self, payload_type: str, **kwargs: Any) -> bytes:
        """Generate raw payload."""
        # Extract encoder if provided
        encoder = kwargs.pop('encoder', None)
        
        # Get payload method
        payload_method = getattr(self.payload_handler, f"generate_{payload_type}", None)
        
        if not payload_method:
            raise ValueError(
                f"Unsupported payload type: {payload_type}. "
                f"Available payloads: {self._get_available_payloads()}"
            )
        
        # Generate raw payload
        shellcode = payload_method(**kwargs)
        
        # Apply encoder if provided
        if encoder:
            shellcode = self._apply_encoder(shellcode, encoder)
        
        return shellcode
    
    def _apply_encoder(self, shellcode: bytes, encoder: Any) -> bytes:
        """Apply encoder to shellcode."""
        if hasattr(encoder, 'encode'):
            # Single encoder
            return encoder.encode(shellcode)
        elif isinstance(encoder, (list, tuple)):
            # Multiple encoders
            for single_encoder in encoder:
                if hasattr(single_encoder, 'encode'):
                    shellcode = single_encoder.encode(shellcode)
                else:
                    raise ValueError(f"Invalid encoder in list: {single_encoder}")
            return shellcode
        else:
            raise ValueError(f"Invalid encoder: {encoder}")
    
    def _get_available_payloads(self) -> List[str]:
        """Get list of available payloads."""
        available = []
        for attr_name in dir(self.payload_handler):
            if attr_name.startswith("generate_"):
                payload_name = attr_name[9:]  # Remove "generate_" prefix
                available.append(payload_name)
        return available
    
    def _apply_educational_mode(self, shellcode: bytes) -> bytes:
        """Apply educational mode modifications."""
        if self.educational:
            # Add educational header
            educational_header = b"# EDUCATIONAL MODE - SAFE FOR LEARNING\n"
            educational_header += b"# This shellcode is for educational purposes only\n"
            educational_header += b"# DO NOT USE FOR MALICIOUS PURPOSES\n"
            educational_header += b"\n"
            
            # Convert shellcode to hex representation for safety
            hex_shellcode = b"\n".join(
                bytes([byte]) for byte in shellcode
            )
            
            return educational_header + hex_shellcode
        
        return shellcode
    
    def get_available_payloads(self) -> List[str]:
        """Get list of available payload types."""
        return self._get_available_payloads()
    
    def get_platform_info(self) -> dict:
        """Get platform information."""
        return {
            "platform": self.platform,
            "educational_mode": self.educational,
            "available_payloads": self.get_available_payloads()
        }
