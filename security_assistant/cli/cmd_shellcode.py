"""
Shellcode command implementation.

Generates shellcode payloads for security testing:
- Platform-specific payloads (Linux, Windows, macOS)
- Encoder support (XOR, Base64)
- Educational mode with safety features
"""

import json
from pathlib import Path

from security_assistant.cli.base import (
    get_logger,
    print_error,
    print_info,
    print_success,
)


def cmd_shellcode(args):
    """
    Generate shellcode payloads for security testing.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Ensure proper encoding for stdout
        import io
        import sys
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        from security_assistant.offensive.authorization import AuthorizationService
        from security_assistant.offensive.shellcode.encoders.base64 import Base64Encoder
        from security_assistant.offensive.shellcode.encoders.xor import XOREncoder
        from security_assistant.offensive.shellcode.generator import ShellcodeGenerator
        
        logger = get_logger(__name__)
        
        # Check ToS acceptance for offensive operations
        auth_service = AuthorizationService()
        if not auth_service.check_tos_accepted() and not args.accept_tos:
            print_error("❌ Terms of Service not accepted. Use --accept-tos to proceed.")
            return 1
        
        # Accept ToS if requested
        if args.accept_tos:
            auth_service.accept_tos()
        
        # Create generator
        generator = ShellcodeGenerator(platform=args.platform, educational=args.educational)
        
        # Determine encoder
        encoder = None
        if args.encoder:
            if args.encoder.lower() == "xor":
                encoder = XOREncoder(key=args.xor_key)
            elif args.encoder.lower() == "base64":
                encoder = Base64Encoder()
            elif args.encoder.lower() == "both":
                # Chain both encoders
                encoder = [XOREncoder(key=args.xor_key), Base64Encoder()]
        
        # Generate payload
        print_info(f"🔧 Generating {args.payload_type} payload for {args.platform}...")
        
        payload_args = {
            "payload_type": args.payload_type,
        }
        
        # Add payload-specific arguments
        if args.payload_type in ["reverse_shell", "bind_shell"]:
            payload_args["lhost"] = args.lhost
            payload_args["lport"] = args.lport
        elif args.payload_type == "exec":
            payload_args["cmd"] = args.cmd
        elif args.payload_type == "download_exec":
            payload_args["url"] = args.url
            payload_args["output"] = args.output
        
        # Generate shellcode
        shellcode = generator.generate(encoder=encoder, **payload_args)
        
        # Save to file if requested
        if args.output_file:
            output_file = Path(args.output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "wb") as f:
                if args.format == "json":
                    # Convert binary to hex for JSON
                    shellcode_hex = shellcode.hex()
                    json.dump({
                        "payload_type": args.payload_type,
                        "platform": args.platform,
                        "encoder": args.encoder,
                        "shellcode": shellcode_hex,
                        "educational": args.educational
                    }, f, indent=2)
                else:
                    f.write(shellcode)
            
            print_success(f"✅ Shellcode saved to: {output_file}")
        else:
            # Print to console
            if args.format == "json":
                # Convert binary to hex for JSON
                shellcode_hex = shellcode.hex()
                result = {
                    "payload_type": args.payload_type,
                    "platform": args.platform,
                    "encoder": args.encoder,
                    "shellcode": shellcode_hex,
                    "educational": args.educational
                }
                print(json.dumps(result, indent=2))
            else:
                print("Generated Shellcode:")
                print("=" * 50)
                if args.educational:
                    # For educational mode, print as hex
                    print(shellcode.hex())
                else:
                    # For raw mode, print binary representation
                    print(repr(shellcode))
                print("=" * 50)
                # Ensure proper flushing
                import sys
                sys.stdout.flush()
        
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Shellcode generation failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
