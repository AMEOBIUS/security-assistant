"""
Example: Scan Python code with Bandit and create GitLab issues.

This script demonstrates the complete workflow:
1. Scan Python files for security vulnerabilities
2. Convert findings to GitLab issues
3. Create issues in GitLab project

Usage:
    python examples/scan_and_create_issues.py --file app.py
    python examples/scan_and_create_issues.py --directory src/ --recursive
    python examples/scan_and_create_issues.py --directory . --group-by-file
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from security_assistant.gitlab_api import GitLabAPI, GitLabAPIError
from security_assistant.scanners.bandit_scanner import BanditScanner, BanditScannerError


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Scan Python code and create GitLab issues for security findings"
    )
    
    # Scan target
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Python file to scan")
    group.add_argument("--directory", help="Directory to scan")
    
    # Scan options
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Scan directory recursively"
    )
    parser.add_argument(
        "--min-severity",
        choices=["LOW", "MEDIUM", "HIGH"],
        default="MEDIUM",
        help="Minimum severity to report (default: MEDIUM)"
    )
    parser.add_argument(
        "--min-confidence",
        choices=["LOW", "MEDIUM", "HIGH"],
        default="MEDIUM",
        help="Minimum confidence to report (default: MEDIUM)"
    )
    
    # GitLab options
    parser.add_argument(
        "--project",
        required=True,
        help="GitLab project ID or path (e.g., 'namespace/project')"
    )
    parser.add_argument(
        "--group-by-file",
        action="store_true",
        help="Create one issue per file instead of one per finding"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't create issues, just show what would be created"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    print("=" * 80)
    print("Bandit Security Scanner → GitLab Issue Creator")
    print("=" * 80)
    print()
    
    # Initialize scanner
    try:
        print("Initializing Bandit scanner...")
        print(f"  Min Severity: {args.min_severity}")
        print(f"  Min Confidence: {args.min_confidence}")
        
        scanner = BanditScanner(
            min_severity=args.min_severity,
            min_confidence=args.min_confidence
        )
        print("✅ Scanner initialized")
        print()
    except BanditScannerError as e:
        print(f"❌ Failed to initialize scanner: {e}")
        return 1
    
    # Run scan
    try:
        if args.file:
            print(f"Scanning file: {args.file}")
            result = scanner.scan_file(args.file)
        else:
            print(f"Scanning directory: {args.directory}")
            print(f"  Recursive: {args.recursive}")
            result = scanner.scan_directory(args.directory, recursive=args.recursive)
        
        print("✅ Scan complete")
        print()
        
        # Display results
        print("Scan Results:")
        print(f"  Files scanned: {result.files_scanned}")
        print(f"  Total findings: {len(result.findings)}")
        print(f"    🔴 High: {result.high_severity_count}")
        print(f"    🟡 Medium: {result.medium_severity_count}")
        print(f"    🟢 Low: {result.low_severity_count}")
        print()
        
        if not result.has_findings:
            print("✅ No security issues found!")
            return 0
        
        # Show findings
        print("Findings:")
        for i, finding in enumerate(result.findings, 1):
            print(f"  {i}. {finding.severity_emoji} {finding.test_name}")
            print(f"     File: {finding.filename}:{finding.line_number}")
            print(f"     Severity: {finding.severity} | Confidence: {finding.confidence}")
            print()
        
    except BanditScannerError as e:
        print(f"❌ Scan failed: {e}")
        return 1
    
    # Convert to GitLab issues
    print("Converting findings to GitLab issues...")
    issues = scanner.scan_result_to_issues(
        result,
        project_name=args.project,
        group_by_file=args.group_by_file
    )
    print(f"✅ Created {len(issues)} issue(s)")
    print()
    
    # Dry run - just show what would be created
    if args.dry_run:
        print("DRY RUN - Issues that would be created:")
        print()
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue.title}")
            print(f"   Labels: {', '.join(issue.labels)}")
            print(f"   Confidential: {issue.confidential}")
            print()
        print("Run without --dry-run to create issues in GitLab")
        return 0
    
    # Create issues in GitLab
    try:
        print("Connecting to GitLab...")
        api = GitLabAPI()
        print(f"✅ Connected to {api.gitlab_url}")
        print()
        
        print(f"Creating issues in project: {args.project}")
        created_issues = []
        
        for i, issue in enumerate(issues, 1):
            print(f"  Creating issue {i}/{len(issues)}: {issue.title}")
            
            try:
                result = api.create_issue(args.project, issue)
                created_issues.append(result)
                print(f"    ✅ Created: {result['web_url']}")
            except GitLabAPIError as e:
                print(f"    ❌ Failed: {e}")
        
        print()
        print("=" * 80)
        print(f"✅ Successfully created {len(created_issues)}/{len(issues)} issues")
        print("=" * 80)
        print()
        
        # Show created issues
        if created_issues:
            print("Created Issues:")
            for issue in created_issues:
                print(f"  • {issue['title']}")
                print(f"    {issue['web_url']}")
                print()
        
        return 0
        
    except GitLabAPIError as e:
        print(f"❌ GitLab API error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
