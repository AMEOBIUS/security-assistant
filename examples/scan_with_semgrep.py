#!/usr/bin/env python3
"""
Semgrep Scanner CLI
Scan code for security vulnerabilities and create GitLab issues.

Usage:
    # Scan single file
    python scan_with_semgrep.py --file app.py --project namespace/project
    
    # Scan directory
    python scan_with_semgrep.py --directory src/ --project namespace/project
    
    # Use specific config
    python scan_with_semgrep.py --directory . --config p/owasp-top-ten --project namespace/project
    
    # Filter by severity
    python scan_with_semgrep.py --directory . --min-severity ERROR --project namespace/project
    
    # Group issues by file
    python scan_with_semgrep.py --directory . --group-by-file --project namespace/project
    
    # Dry run (don't create issues)
    python scan_with_semgrep.py --directory . --project namespace/project --dry-run
    
    # Custom rules
    python scan_with_semgrep.py --directory . --custom-rules rules.yaml --project namespace/project
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.gitlab_api import GitLabAPI
from security_assistant.scanners.semgrep_scanner import (
    SemgrepNotInstalledError,
    SemgrepScanner,
    SemgrepScannerError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan code with Semgrep and create GitLab issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Scan target
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--file",
        help="Scan a single file"
    )
    target_group.add_argument(
        "--directory",
        help="Scan a directory"
    )
    
    # Semgrep options
    parser.add_argument(
        "--config",
        default="auto",
        help="Semgrep config/ruleset (default: auto). Options: auto, p/security-audit, p/owasp-top-ten, p/ci, or path to custom rules"
    )
    parser.add_argument(
        "--min-severity",
        choices=["INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Minimum severity to report (default: INFO)"
    )
    parser.add_argument(
        "--custom-rules",
        action="append",
        help="Additional custom rule files/URLs (can be specified multiple times)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="Directories to exclude (can be specified multiple times)"
    )
    
    # GitLab options
    parser.add_argument(
        "--project",
        required=True,
        help="GitLab project (namespace/project)"
    )
    parser.add_argument(
        "--token",
        help="GitLab API token (or set GITLAB_TOKEN env var)"
    )
    parser.add_argument(
        "--gitlab-url",
        default="https://gitlab.com",
        help="GitLab instance URL (default: https://gitlab.com)"
    )
    
    # Issue options
    parser.add_argument(
        "--group-by-file",
        action="store_true",
        help="Create one issue per file instead of one per finding"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview issues without creating them"
    )
    
    return parser.parse_args()


def print_summary(scan_result, issues):
    """Print scan summary."""
    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    print(f"Files scanned: {scan_result.files_scanned}")
    print(f"Languages detected: {', '.join(sorted(scan_result.languages)) if scan_result.languages else 'None'}")
    print("\nFindings:")
    print(f"  🔴 Errors:   {scan_result.error_count}")
    print(f"  🟡 Warnings: {scan_result.warning_count}")
    print(f"  🟢 Info:     {scan_result.info_count}")
    print(f"  Total:       {len(scan_result.findings)}")
    
    if scan_result.errors:
        print(f"\nScan errors: {len(scan_result.errors)}")
        for error in scan_result.errors[:5]:  # Show first 5
            print(f"  - {error}")
    
    print(f"\nIssues to create: {len(issues)}")
    print("=" * 70)


def print_issue_preview(issue, index):
    """Print issue preview."""
    print(f"\n--- Issue {index} ---")
    print(f"Title: {issue.title}")
    print(f"Labels: {', '.join(issue.labels)}")
    print(f"Confidential: {issue.confidential}")
    print("\nDescription preview:")
    lines = issue.description.split('\n')
    for line in lines[:10]:  # Show first 10 lines
        print(f"  {line}")
    if len(lines) > 10:
        print(f"  ... ({len(lines) - 10} more lines)")


def main():
    """Main function."""
    args = parse_args()
    
    # Get GitLab token from environment or args
    # Priority: --token argument > GITLAB_TOKEN env var
    token = args.token or os.getenv("GITLAB_TOKEN")
    if not token and not args.dry_run:
        logger.error("GitLab token required. Set GITLAB_TOKEN env var or use --token")
        logger.error("Get project token from: Project Settings > Access Tokens")
        return 1
    
    try:
        # Initialize scanner
        logger.info("Initializing Semgrep scanner...")
        scanner = SemgrepScanner(
            min_severity=args.min_severity,
            config=args.config,
            exclude_dirs=args.exclude,
            custom_rules=args.custom_rules
        )
        
        # Scan
        if args.file:
            logger.info(f"Scanning file: {args.file}")
            scan_result = scanner.scan_file(args.file)
        else:
            logger.info(f"Scanning directory: {args.directory}")
            scan_result = scanner.scan_directory(args.directory)
        
        # Convert to issues
        logger.info("Converting findings to GitLab issues...")
        issues = scanner.scan_result_to_issues(
            scan_result,
            project_name=args.project,
            group_by_file=args.group_by_file
        )
        
        # Print summary
        print_summary(scan_result, issues)
        
        # Dry run - just preview
        if args.dry_run:
            print("\n🔍 DRY RUN - Preview of issues to be created:")
            for i, issue in enumerate(issues, 1):
                print_issue_preview(issue, i)
            print("\n✅ Dry run complete. No issues created.")
            return 0
        
        # Create issues
        if not issues:
            print("\n✅ No issues to create.")
            return 0
        
        logger.info(f"Creating {len(issues)} issues in GitLab...")
        gitlab = GitLabAPI(token=token, gitlab_url=args.gitlab_url)
        
        created_count = 0
        failed_count = 0
        
        for i, issue in enumerate(issues, 1):
            try:
                logger.info(f"Creating issue {i}/{len(issues)}: {issue.title}")
                created = gitlab.create_issue(
                    project_id=args.project,
                    issue_data=issue
                )
                created_count += 1
                print(f"✅ Created: {created.get('web_url', 'N/A')}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to create issue: {str(e)}")
        
        # Final summary
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"✅ Created: {created_count}")
        if failed_count > 0:
            print(f"❌ Failed:  {failed_count}")
        print("=" * 70)
        
        return 0 if failed_count == 0 else 1
        
    except SemgrepNotInstalledError:
        logger.error("Semgrep is not installed. Install with: pip install semgrep")
        return 1
    except SemgrepScannerError as e:
        logger.error(f"Scan error: {str(e)}")
        return 1
    except KeyboardInterrupt:
        logger.info("\nScan cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
