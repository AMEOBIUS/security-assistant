"""
Test shellcode CLI integration.
"""

import tempfile
from pathlib import Path

from security_assistant.cli.cmd_shellcode import cmd_shellcode
from security_assistant.offensive.authorization import AuthorizationService


def test_shellcode_cli_exec_payload():
    """Test CLI command for generating exec payload."""
    # Setup
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock args
    class MockArgs:
        payload_type = "exec"
        platform = "linux-x64"
        cmd = "echo hello"
        educational = True
        accept_tos = True
        verbose = False
        encoder = None
        xor_key = 0x55
        output_file = None
        format = "text"
    
    args = MockArgs()
    
    # Test execution
    result = cmd_shellcode(args)
    assert result == 0, "CLI command should succeed"


def test_shellcode_cli_with_encoder():
    """Test CLI command with XOR encoder."""
    # Setup
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock args
    class MockArgs:
        payload_type = "exec"
        platform = "linux-x64"
        cmd = "whoami"
        educational = True
        accept_tos = True
        verbose = False
        encoder = "xor"
        xor_key = 0xAA
        output_file = None
        format = "text"
    
    args = MockArgs()
    
    # Test execution
    result = cmd_shellcode(args)
    assert result == 0, "CLI command with encoder should succeed"


def test_shellcode_cli_json_output():
    """Test CLI command with JSON output format."""
    # Setup
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock args
    class MockArgs:
        payload_type = "reverse_shell"
        platform = "linux-x64"
        lhost = "127.0.0.1"
        lport = 4444
        educational = True
        accept_tos = True
        verbose = False
        encoder = None
        xor_key = 0x55
        output_file = None
        format = "json"
    
    args = MockArgs()
    
    # Test execution
    result = cmd_shellcode(args)
    assert result == 0, "CLI command with JSON format should succeed"


def test_shellcode_cli_file_output():
    """Test CLI command with file output."""
    # Setup
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file_path = Path(temp_dir) / "shellcode.bin"
        
        # Mock args
        class MockArgs:
            payload_type = "exec"
            platform = "linux-x64"
            cmd = "ls -la"
            educational = False
            accept_tos = True
            verbose = False
            encoder = None
            xor_key = 0x55
            output_file = str(output_file_path)
            format = "text"
        
        args = MockArgs()
        
        # Test execution
        result = cmd_shellcode(args)
        assert result == 0, "CLI command with file output should succeed"
        assert output_file_path.exists(), "Output file should be created"
        assert output_file_path.stat().st_size > 0, "Output file should not be empty"


def test_shellcode_cli_tos_rejection():
    """Test CLI command rejects without ToS acceptance."""
    # Reset ToS acceptance
    auth_service = AuthorizationService()
    auth_service.reject_tos()
    
    # Mock args without ToS acceptance
    class MockArgs:
        payload_type = "exec"
        platform = "linux-x64"
        cmd = "echo test"
        educational = True
        accept_tos = False
        verbose = False
        encoder = None
        xor_key = 0x55
        output_file = None
        format = "text"
    
    args = MockArgs()
    
    # Test execution should fail
    result = cmd_shellcode(args)
    assert result == 1, "CLI command should fail without ToS acceptance"


if __name__ == "__main__":
    test_shellcode_cli_exec_payload()
    test_shellcode_cli_with_encoder()
    test_shellcode_cli_json_output()
    test_shellcode_cli_file_output()
    test_shellcode_cli_tos_rejection()
    print("✅ All shellcode CLI tests passed!")
