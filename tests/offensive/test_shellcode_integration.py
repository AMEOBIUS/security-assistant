"""
Integration test for shellcode generator with vulnerable lab environment.
"""

import subprocess
import tempfile
from pathlib import Path


def test_shellcode_cli_integration():
    """Test full CLI integration with shellcode generation."""
    
    # Test 1: Help command works
    result = subprocess.run([
        "python", "-c", 
        "from security_assistant.cli import main; import sys; "
        "sys.argv = ['security-assistant', 'shellcode', '--help']; "
        "main()"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, f"CLI help should succeed: {result.stderr}"
    assert "Generate shellcode payloads" in result.stdout, "Should contain help text"
    
    # Test 2: File output (using existing test approach)
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file_path = Path(temp_dir) / "test_shellcode.bin"
        
        # Use the same approach as the unit tests
        from security_assistant.offensive.authorization import AuthorizationService
        
        # Accept ToS first
        auth_service = AuthorizationService()
        auth_service.accept_tos()
        
        # Import and call the CLI command function
        from security_assistant.cli.cmd_shellcode import cmd_shellcode
        
        # Setup args
        class MockArgs:
            payload_type = "exec"
            platform = "linux-x64"
            cmd = "whoami"
            educational = True
            accept_tos = True
            verbose = False
            encoder = None
            xor_key = 0x55
            output_file = str(output_file_path)
            format = "text"
        
        args = MockArgs()
        
        # Execute
        result = cmd_shellcode(args)
        assert result == 0, "CLI command should succeed"
        assert output_file_path.exists(), "Output file should be created"
        assert output_file_path.stat().st_size > 0, "Output file should not be empty"
    
    print("✅ All integration tests passed!")


def test_vulnerable_lab_environment():
    """Test that vulnerable lab environment is properly set up."""
    
    # Check that vulnerable lab app exists
    from pathlib import Path
    base_dir = Path(__file__).parent.parent.parent
    vulnerable_app = base_dir / "examples" / "vulnerable_lab_app.py"
    assert vulnerable_app.exists(), f"Vulnerable lab app should exist at {vulnerable_app}"
    
    # Check that it contains expected vulnerabilities
    content = vulnerable_app.read_text()
    assert "subprocess.run" in content, "Should contain command execution"
    assert "shell=True" in content, "Should contain shell=True vulnerability"
    assert "eval(" in content, "Should contain eval vulnerability"
    assert "pickle.loads" in content, "Should contain unsafe deserialization"
    
    print("✅ Vulnerable lab environment test passed!")


if __name__ == "__main__":
    test_shellcode_cli_integration()
    test_vulnerable_lab_environment()
    print("🎉 All integration tests completed successfully!")
