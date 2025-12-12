"""
Shellcode generator tests
Tests for platform-specific shellcode generation with encoders
"""

import pytest

from security_assistant.offensive.shellcode.encoders.base64 import Base64Encoder
from security_assistant.offensive.shellcode.encoders.xor import XOREncoder
from security_assistant.offensive.shellcode.generator import ShellcodeGenerator


def test_shellcode_generator_initialization():
    """Test ShellcodeGenerator initialization."""
    gen = ShellcodeGenerator(platform="linux-x64")
    assert gen.platform == "linux-x64"
    assert not gen.educational


def test_shellcode_generator_educational_mode():
    """Test educational mode."""
    gen = ShellcodeGenerator(platform="linux-x64", educational=True)
    assert gen.educational


def test_linux_reverse_shell_generation():
    """Test Linux reverse shell payload generation."""
    gen = ShellcodeGenerator(platform="linux-x64")
    gen._skip_auth = True  # Skip auth for testing
    shellcode = gen.generate(
        payload_type="reverse_shell",
        lhost="127.0.0.1",
        lport=4444
    )
    assert shellcode
    assert len(shellcode) > 0
    assert isinstance(shellcode, bytes)


def test_windows_exec_payload():
    """Test Windows execute command payload."""
    gen = ShellcodeGenerator(platform="windows-x64")
    gen._skip_auth = True  # Skip auth for testing
    shellcode = gen.generate(
        payload_type="exec",
        cmd="calc.exe"
    )
    assert shellcode
    assert len(shellcode) > 0
    assert isinstance(shellcode, bytes)


def test_macos_bind_shell():
    """Test macOS bind shell payload."""
    gen = ShellcodeGenerator(platform="macos-x64")
    gen._skip_auth = True  # Skip auth for testing
    shellcode = gen.generate(
        payload_type="bind_shell",
        lport=8080
    )
    assert shellcode
    assert len(shellcode) > 0
    assert isinstance(shellcode, bytes)


def test_xor_encoder():
    """Test XOR encoder."""
    encoder = XOREncoder(key=0xAA)
    original = b"\x90\x90\x90\x90"
    encoded = encoder.encode(original)
    decoded = encoder.decode(encoded)
    assert decoded == original


def test_base64_encoder():
    """Test Base64 encoder."""
    encoder = Base64Encoder()
    original = b"test shellcode"
    encoded = encoder.encode(original)
    decoded = encoder.decode(encoded)
    assert decoded == original


def test_educational_mode_safety():
    """Test educational mode returns safe version."""
    gen = ShellcodeGenerator(platform="linux-x64", educational=True)
    gen._skip_auth = True  # Skip auth for testing
    shellcode = gen.generate(payload_type="reverse_shell", lhost="127.0.0.1", lport=4444)
    # Should return commented/safe version
    shellcode_str = str(shellcode)
    assert "EDUCATIONAL" in shellcode_str or "SAFE MODE" in shellcode_str


def test_unsupported_platform():
    """Test unsupported platform error."""
    with pytest.raises(ValueError, match="Unsupported platform"):
        gen = ShellcodeGenerator(platform="android-arm")


def test_unsupported_payload():
    """Test unsupported payload type error."""
    gen = ShellcodeGenerator(platform="linux-x64")
    gen._skip_auth = True  # Skip auth for testing
    with pytest.raises(ValueError, match="Unsupported payload type"):
        gen.generate(payload_type="unknown-payload")


def test_payload_with_encoder():
    """Test payload generation with encoder."""
    gen = ShellcodeGenerator(platform="linux-x64")
    gen._skip_auth = True  # Skip auth for testing
    encoder = XOREncoder(key=0x55)
    
    shellcode = gen.generate(
        payload_type="reverse_shell",
        lhost="127.0.0.1",
        lport=4444,
        encoder=encoder
    )
    
    assert shellcode
    assert len(shellcode) > 0
    assert isinstance(shellcode, bytes)


def test_multiple_encoders():
    """Test chaining multiple encoders."""
    gen = ShellcodeGenerator(platform="linux-x64")
    gen._skip_auth = True  # Skip auth for testing
    xor_encoder = XOREncoder(key=0xAA)
    base64_encoder = Base64Encoder()
    
    shellcode = gen.generate(
        payload_type="exec",
        cmd="echo test",
        encoder=[xor_encoder, base64_encoder]
    )
    
    assert shellcode
    assert len(shellcode) > 0


def test_invalid_encoder():
    """Test invalid encoder error."""
    gen = ShellcodeGenerator(platform="linux-x64")
    gen._skip_auth = True  # Skip auth for testing
    
    # Test with an object that doesn't have encode method
    class InvalidEncoder:
        pass
    
    with pytest.raises(ValueError, match="Invalid encoder"):
        gen.generate(
            payload_type="reverse_shell",
            lhost="127.0.0.1",
            lport=4444,
            encoder=InvalidEncoder()
        )
