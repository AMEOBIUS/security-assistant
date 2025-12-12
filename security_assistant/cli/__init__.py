"""
Security Assistant CLI - Command-line interface refactored into modules.

This replaces the monolithic cli.py with a modular structure:
- cli/__init__.py - Main entry point
- cli/base.py - Common utilities
- cli/cmd_*.py - Command implementations
"""

import argparse
import sys
from pathlib import Path

from security_assistant.cli.base import print_banner, setup_logging
from security_assistant.cli.cmd_chat import cmd_chat
from security_assistant.cli.cmd_config import cmd_config
from security_assistant.cli.cmd_explain import cmd_explain
from security_assistant.cli.cmd_poc import cmd_poc
from security_assistant.cli.cmd_query import cmd_query
from security_assistant.cli.cmd_report import cmd_report
from security_assistant.cli.cmd_scan import cmd_scan
from security_assistant.cli.cmd_shellcode import cmd_shellcode

__version__ = "1.0.0"


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="security-assistant",
        description="Security Assistant - CLI interface for security scanning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  security-assistant scan .

  # Scan with specific scanners
  security-assistant scan --bandit --semgrep src/

  # Scan with custom config
  security-assistant scan --config security-assistant.yaml

  # Generate reports only
  security-assistant report --format html,markdown

  # Create default config
  security-assistant config --create
        """
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Security Assistant {__version__}",
        help="Show version information",
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Available commands",
        metavar="{scan,config,report,poc,explain,query,chat}"
    )

    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Run security scan on targets",
        description="Execute comprehensive security scan on files or directories"
    )
    scan_parser.add_argument(
        "targets",
        nargs="*",
        help="Target files or directories to scan (default: .)",
        default=["."],
    )
    scan_parser.add_argument(
        "--targets-file",
        help="File with list of targets (one per line)",
    )
    scan_parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    scan_parser.add_argument(
        "--no-env",
        action="store_true",
        help="Ignore environment variables",
    )
    scan_parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports)",
    )
    scan_parser.add_argument(
        "--format",
        help="Report format(s) (comma-separated: json,html,markdown,xml,sarif)",
    )
    scan_parser.add_argument(
        "--preset",
        choices=["quick", "full", "ci"],
        help="Use predefined configuration preset",
    )
    scanner_group = scan_parser.add_mutually_exclusive_group()
    scanner_group.add_argument(
        "--bandit-only",
        action="store_true",
        help="Only run Bandit scanner",
    )
    scanner_group.add_argument(
        "--semgrep-only",
        action="store_true",
        help="Only run Semgrep scanner",
    )
    scanner_group.add_argument(
        "--trivy-only",
        action="store_true",
        help="Only run Trivy scanner",
    )
    scanner_group.add_argument(
        "--nuclei-only",
        action="store_true",
        help="Only run Nuclei scanner",
    )
    scanner_group.add_argument(
        "--no-bandit",
        action="store_true",
        help="Disable Bandit scanner",
    )
    scanner_group.add_argument(
        "--no-semgrep",
        action="store_true",
        help="Disable Semgrep scanner",
    )
    scanner_group.add_argument(
        "--no-trivy",
        action="store_true",
        help="Disable Trivy scanner",
    )
    scanner_group.add_argument(
        "--no-nuclei",
        action="store_true",
        help="Disable Nuclei scanner",
    )
    scan_parser.add_argument(
        "--dedup",
        choices=["smart", "exact", "none"],
        default="smart",
        help="Deduplication strategy for findings",
    )
    scan_parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of concurrent scanners",
    )
    scan_parser.add_argument(
        "--no-kev",
        action="store_true",
        help="Disable KEV database lookup",
    )
    scan_parser.add_argument(
        "--no-fp-detection",
        action="store_true",
        help="Disable false positive detection",
    )
    scan_parser.add_argument(
        "--no-reachability",
        action="store_true",
        help="Disable reachability analysis",
    )
    scan_parser.add_argument(
        "--fail-on-critical",
        action=argparse.BooleanOptionalAction,
        help="Fail scan if critical findings detected",
    )
    scan_parser.add_argument(
        "--fail-on-high",
        action=argparse.BooleanOptionalAction,
        help="Fail scan if high severity findings detected",
    )
    scan_parser.add_argument(
        "--open",
        action="store_true",
        help="Open generated HTML report in browser",
    )
    scan_parser.add_argument(
        "--explain",
        action="store_true",
        help="Explain top findings with AI",
    )
    scan_parser.add_argument(
        "--llm",
        choices=["claude-3-5-haiku", "gpt-3.5-turbo", "gemini-1.5-flash"],
        help="AI model for explanation features",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # Shellcode command
    shellcode_parser = subparsers.add_parser(
        "shellcode",
        help="Generate shellcode payloads for security testing",
        description="Generate shellcode payloads for security testing and research"
    )
    shellcode_parser.add_argument(
        "--payload-type",
        choices=["exec", "reverse_shell", "bind_shell", "download_exec"],
        required=True,
        help="Type of payload to generate"
    )
    shellcode_parser.add_argument(
        "--platform",
        choices=["linux-x64", "windows-x64", "macos-x64"],
        required=True,
        help="Target platform"
    )
    shellcode_parser.add_argument(
        "--cmd",
        help="Command to execute (for exec payload)"
    )
    shellcode_parser.add_argument(
        "--lhost",
        help="Listener host (for reverse_shell)"
    )
    shellcode_parser.add_argument(
        "--lport",
        type=int,
        help="Listener port (for reverse_shell)"
    )
    shellcode_parser.add_argument(
        "--url",
        help="URL to download (for download_exec)"
    )
    shellcode_parser.add_argument(
        "--output",
        help="Output file path for downloaded file (for download_exec)"
    )
    shellcode_parser.add_argument(
        "--encoder",
        choices=["xor", "base64", "both"],
        help="Encoder to use"
    )
    shellcode_parser.add_argument(
        "--xor-key",
        type=int,
        default=0x55,
        help="XOR key for encoding (default: 0x55)"
    )
    shellcode_parser.add_argument(
        "--educational",
        action="store_true",
        help="Enable educational mode (safe, non-functional payloads)"
    )
    shellcode_parser.add_argument(
        "--accept-tos",
        action="store_true",
        help="Accept Terms of Service for offensive tools"
    )
    shellcode_parser.add_argument(
        "--output-file",
        help="Path to save generated shellcode"
    )
    shellcode_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    shellcode_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    shellcode_parser.set_defaults(func=cmd_shellcode)

    return parser


def main(argv=None) -> int:
    """Main CLI entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args(argv)

        # Setup basic if no command specified
        if not hasattr(args, 'command'):
            parser.print_help()
            return 0

        # Setup logging
        setup_logging(getattr(args, 'verbose', False), getattr(args, 'log_file', None))

        # Print banner
        print_banner()

        # Execute command
        if hasattr(args, 'func'):
            return args.func(args)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
