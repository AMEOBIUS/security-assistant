"""
CLI Commands for SQLMap Integration

Provides command-line interface for SQLMap scanner with the following commands:
- sqlmap-quick: Quick SQL injection scan
- sqlmap-full: Comprehensive SQL injection scan  
- sqlmap-custom: Custom SQLMap scan with parameters

Usage:
    security-assistant sqlmap-quick --url "http://example.com/test.php?id=1" --params "id"
    security-assistant sqlmap-full --url "http://example.com/login.php" --params "username,password"
    security-assistant sqlmap-custom --url "http://example.com/api" --params "id" --level 3 --risk 2
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict

from security_assistant.offensive.scanners.sqlmap_scanner import (
    SQLMapNotInstalledError,
    SQLMapScanner,
)

logger = logging.getLogger(__name__)


def register_sqlmap_commands(subparsers):
    """Register SQLMap CLI commands."""
    # Quick scan command
    quick_parser = subparsers.add_parser(
        "sqlmap-quick",
        help="Quick SQL injection scan (level 1, risk 1)",
        description="Perform quick SQL injection scan using SQLMap"
    )
    quick_parser.add_argument(
        "--url",
        required=True,
        help="Target URL to scan"
    )
    quick_parser.add_argument(
        "--params",
        help="Comma-separated list of GET parameters to test"
    )
    quick_parser.add_argument(
        "--data",
        help="POST data to test (e.g., 'username=admin&password=test')"
    )
    quick_parser.set_defaults(func=handle_sqlmap_quick)
    
    # Full scan command
    full_parser = subparsers.add_parser(
        "sqlmap-full",
        help="Comprehensive SQL injection scan (level 5, risk 3)",
        description="Perform comprehensive SQL injection scan using SQLMap"
    )
    full_parser.add_argument(
        "--url",
        required=True,
        help="Target URL to scan"
    )
    full_parser.add_argument(
        "--params",
        help="Comma-separated list of GET parameters to test"
    )
    full_parser.add_argument(
        "--data",
        help="POST data to test (e.g., 'username=admin&password=test')"
    )
    full_parser.set_defaults(func=handle_sqlmap_full)
    
    # Custom scan command
    custom_parser = subparsers.add_parser(
        "sqlmap-custom",
        help="Custom SQLMap scan with advanced parameters",
        description="Perform custom SQLMap scan with full parameter control"
    )
    custom_parser.add_argument(
        "--url",
        required=True,
        help="Target URL to scan"
    )
    custom_parser.add_argument(
        "--params",
        help="Comma-separated list of GET parameters to test"
    )
    custom_parser.add_argument(
        "--data",
        help="POST data to test (e.g., 'username=admin&password=test')"
    )
    custom_parser.add_argument(
        "--level",
        type=int,
        default=1,
        choices=range(1, 6),
        help="Test level (1-5, default: 1)"
    )
    custom_parser.add_argument(
        "--risk",
        type=int,
        default=1,
        choices=range(1, 4),
        help="Risk level (1-3, default: 1)"
    )
    custom_parser.add_argument(
        "--batch",
        action="store_true",
        help="Run in batch mode (non-interactive)"
    )
    custom_parser.add_argument(
        "--output",
        choices=["json", "xml"],
        default="json",
        help="Output format (json or xml, default: json)"
    )
    custom_parser.set_defaults(func=handle_sqlmap_custom)


def handle_sqlmap_quick(args):
    """Handle sqlmap-quick command."""
    try:
        scanner = SQLMapScanner()
        
        # Parse parameters
        params = args.params.split(",") if args.params else None
        
        logger.info(f"Starting quick SQLMap scan on: {args.url}")
        logger.info(f"Parameters: {params or 'auto-detect'}")
        
        result = scanner.quick_scan(
            target=args.url,
            params=params,
            data=args.data
        )
        
        _display_results(result, "quick")
        
    except SQLMapNotInstalledError as e:
        logger.error(f"SQLMap not installed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Quick scan failed: {e}")
        sys.exit(1)


def handle_sqlmap_full(args):
    """Handle sqlmap-full command."""
    try:
        scanner = SQLMapScanner()
        
        # Parse parameters
        params = args.params.split(",") if args.params else None
        
        logger.info(f"Starting full SQLMap scan on: {args.url}")
        logger.info(f"Parameters: {params or 'auto-detect'}")
        
        result = scanner.full_scan(
            target=args.url,
            params=params,
            data=args.data
        )
        
        _display_results(result, "full")
        
    except SQLMapNotInstalledError as e:
        logger.error(f"SQLMap not installed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Full scan failed: {e}")
        sys.exit(1)


def handle_sqlmap_custom(args):
    """Handle sqlmap-custom command."""
    try:
        scanner = SQLMapScanner()
        
        # Parse parameters
        params = args.params.split(",") if args.params else None
        
        logger.info(f"Starting custom SQLMap scan on: {args.url}")
        logger.info(f"Parameters: {params or 'auto-detect'}")
        logger.info(f"Level: {args.level}, Risk: {args.risk}")
        
        result = scanner.scan(
            target=args.url,
            params=params,
            data=args.data,
            level=args.level,
            risk=args.risk,
            batch=args.batch,
            output_format=args.output
        )
        
        _display_results(result, "custom")
        
    except SQLMapNotInstalledError as e:
        logger.error(f"SQLMap not installed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Custom scan failed: {e}")
        sys.exit(1)


def _display_results(result: Dict, scan_type: str):
    """Display scan results in human-readable format."""
    print("\n" + "="*60)
    print(f"SQLMap Scan Results ({scan_type.upper()} SCAN)")
    print("="*60)
    
    print(f"\nTarget: {result.get('target', 'unknown')}")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Timestamp: {result.get('timestamp', 'unknown')}")
    
    if "vulnerabilities" in result and result["vulnerabilities"]:
        print(f"\n🚨 Found {len(result['vulnerabilities'])} vulnerabilities:")
        print("-" * 60)
        
        for i, vuln in enumerate(result["vulnerabilities"], 1):
            print(f"\nVulnerability #{i}:")
            print(f"  Type: {vuln.get('type', 'unknown')}")
            print(f"  Parameter: {vuln.get('parameter', 'unknown')}")
            print(f"  Severity: {vuln.get('severity', 'unknown')}")
            print(f"  Description: {vuln.get('description', 'N/A')}")
            if vuln.get('payload'):
                print(f"  Payload: {vuln.get('payload')}")
        
        print("\n" + "="*60)
        print("⚠️  RECOMMENDATION: Review and fix vulnerabilities immediately!")
        print("="*60)
    else:
        print("\n✅ No vulnerabilities found")
        print("="*60)
    
    # Save results to file
    output_file = f"sqlmap_results_{scan_type}_{result.get('target', 'scan').replace('://', '_').replace('/', '_')}.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📁 Results saved to: {Path(output_file).resolve()}")
    except Exception as e:
        logger.warning(f"Failed to save results: {e}")


def get_sqlmap_help() -> str:
    """Return SQLMap CLI help information."""
    return """
SQLMap Integration - CLI Commands

Available commands:
  1. sqlmap-quick   - Quick scan (level 1, risk 1)
  2. sqlmap-full    - Full scan (level 5, risk 3)
  3. sqlmap-custom  - Custom scan with parameters

Examples:
  # Quick scan with GET parameter
  security-assistant sqlmap-quick --url "http://example.com/test.php?id=1" --params "id"

  # Full scan with POST data
  security-assistant sqlmap-full --url "http://example.com/login.php" --data "username=admin&password=test"

  # Custom scan with specific level and risk
  security-assistant sqlmap-custom --url "http://example.com/api" --params "id" --level 3 --risk 2 --batch

Notes:
  - SQLMap must be installed and in PATH
  - All targets must be authorized via: security-assistant authorize --add TARGET
  - Results are automatically saved to JSON files
"""


if __name__ == "__main__":
    # Test command registration
    parser = argparse.ArgumentParser(description="SQLMap CLI Test")
    subparsers = parser.add_subparsers(title="SQLMap commands", dest="command")
    
    register_sqlmap_commands(subparsers)
    
    if len(sys.argv) == 1:
        print(get_sqlmap_help())
    else:
        args = parser.parse_args()
        if hasattr(args, 'func'):
            args.func(args)
