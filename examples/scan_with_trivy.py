#!/usr/bin/env python3
"""
Trivy Scanner CLI - Scan containers and filesystems for vulnerabilities

This script provides a command-line interface for scanning with Trivy and
optionally creating GitLab issues for findings.

Usage:
    # Scan a container image
    python scan_with_trivy.py --image alpine:3.15 --project test/project

    # Scan a filesystem
    python scan_with_trivy.py --directory /path/to/project --project test/project

    # Scan with multiple scanners
    python scan_with_trivy.py --image nginx:latest --scanners vuln,secret,config --project test/project

    # Generate SBOM
    python scan_with_trivy.py --image alpine:3.15 --sbom --sbom-format cyclonedx

    # Dry-run (preview without creating issues)
    python scan_with_trivy.py --image alpine:3.15 --project test/project --dry-run

    # Group issues by severity
    python scan_with_trivy.py --image alpine:3.15 --project test/project --group-by-severity

    # Scan with custom severity threshold
    python scan_with_trivy.py --image alpine:3.15 --min-severity CRITICAL --project test/project

Requirements:
    - Trivy installed (https://aquasecurity.github.io/trivy/)
    - GitLab personal access token (for creating issues)
    - Python 3.8+
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.scanners.trivy_scanner import (
    TrivyScanner,
    TrivySeverity,
    TrivyScanType,
    TrivyScannerError,
    TrivyNotInstalledError,
)
from security_assistant.gitlab_client import GitLabClient


def print_banner():
    """Print CLI banner"""
    print("=" * 70)
    print("  Trivy Scanner CLI - Container & Filesystem Security Scanner")
    print("=" * 70)
    print()


def print_scan_summary(scan_result):
    """Print scan result summary"""
    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    print(f"Target:              {scan_result.target}")
    print(f"Scan Type:           {scan_result.scan_type.value}")
    print(f"Scan Time:           {scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Total Findings:      {len(scan_result.findings)}")
    print(f"  Vulnerabilities:   {scan_result.vulnerability_count}")
    print(f"  Secrets:           {scan_result.secret_count}")
    print(f"  Misconfigurations: {scan_result.misconfig_count}")
    print()
    print("Severity Breakdown:")
    print(f"  🔴 CRITICAL:       {scan_result.critical_count}")
    print(f"  🟠 HIGH:           {scan_result.high_count}")
    print(f"  🟡 MEDIUM:         {scan_result.medium_count}")
    print(f"  🟢 LOW:            {scan_result.low_count}")
    print()
    print(f"Fixable:             {scan_result.fixable_count}/{scan_result.vulnerability_count}")
    
    if scan_result.packages:
        print(f"\nAffected Packages:   {', '.join(sorted(scan_result.packages)[:10])}")
        if len(scan_result.packages) > 10:
            print(f"                     ... and {len(scan_result.packages) - 10} more")
    
    print("=" * 70)


def print_findings_detail(scan_result, max_findings: int = 10):
    """Print detailed findings"""
    if not scan_result.has_findings:
        print("\n✅ No security issues found!")
        return
    
    print(f"\n{'=' * 70}")
    print(f"TOP {min(max_findings, len(scan_result.findings))} FINDINGS")
    print("=" * 70)
    
    # Sort by severity
    sorted_findings = sorted(
        scan_result.findings,
        key=lambda f: TrivyScanner.SEVERITY_PRIORITY[f.severity],
        reverse=True
    )
    
    for i, finding in enumerate(sorted_findings[:max_findings], 1):
        print(f"\n{i}. {finding.severity_emoji} {finding.vulnerability_id or finding.title}")
        print(f"   Severity:  {finding.severity.value}")
        print(f"   Package:   {finding.pkg_name}")
        
        if finding.pkg_type == "secret":
            print(f"   Location:  Lines {finding.start_line}-{finding.end_line}")
        elif finding.installed_version:
            print(f"   Installed: {finding.installed_version}")
            if finding.fixed_version:
                print(f"   Fixed:     {finding.fixed_version}")
            else:
                print(f"   Fixed:     Not available")
        
        if finding.cvss_score:
            print(f"   CVSS:      {finding.cvss_score}")
        
        # Truncate description
        desc = finding.description[:150]
        if len(finding.description) > 150:
            desc += "..."
        print(f"   Details:   {desc}")
    
    if len(scan_result.findings) > max_findings:
        print(f"\n... and {len(scan_result.findings) - max_findings} more findings")
    
    print("=" * 70)


def create_gitlab_issues(scan_result, project_name: str, gitlab_url: str, token: str, group_by_severity: bool = False):
    """Create GitLab issues from scan results"""
    print(f"\n{'=' * 70}")
    print("CREATING GITLAB ISSUES")
    print("=" * 70)
    
    try:
        # Initialize scanner and GitLab client
        scanner = TrivyScanner()
        client = GitLabClient(gitlab_url=gitlab_url, private_token=token)
        
        # Convert findings to issues
        issues = scanner.scan_result_to_issues(
            scan_result,
            project_name,
            group_by_severity=group_by_severity
        )
        
        print(f"Creating {len(issues)} issue(s) in {project_name}...")
        print()
        
        created_count = 0
        for issue in issues:
            try:
                created_issue = client.create_issue(
                    project_name,
                    issue.title,
                    issue.description,
                    labels=issue.labels,
                    confidential=issue.confidential,
                )
                
                created_count += 1
                print(f"✅ Created: {issue.title}")
                print(f"   URL: {created_issue.get('web_url', 'N/A')}")
                print()
                
            except Exception as e:
                print(f"❌ Failed to create issue: {issue.title}")
                print(f"   Error: {e}")
                print()
        
        print("=" * 70)
        print(f"Successfully created {created_count}/{len(issues)} issues")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error creating GitLab issues: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Scan containers and filesystems with Trivy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan container image
  %(prog)s --image alpine:3.15 --project test/project

  # Scan filesystem with multiple scanners
  %(prog)s --directory /app --scanners vuln,secret,config --project test/project

  # Generate SBOM
  %(prog)s --image nginx:latest --sbom --sbom-format cyclonedx --sbom-output sbom.json

  # Dry-run (preview without creating issues)
  %(prog)s --image alpine:3.15 --project test/project --dry-run

  # Group issues by severity
  %(prog)s --image alpine:3.15 --project test/project --group-by-severity

Environment Variables:
  GITLAB_TOKEN     GitLab personal access token
  GITLAB_URL       GitLab instance URL (default: https://gitlab.com)
        """
    )
    
    # Scan target (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--image",
        help="Container image to scan (e.g., alpine:3.15, nginx:latest)"
    )
    target_group.add_argument(
        "--directory",
        help="Directory path to scan"
    )
    target_group.add_argument(
        "--repository",
        help="Git repository URL to scan"
    )
    
    # Scanner options
    parser.add_argument(
        "--scanners",
        default="vuln",
        help="Comma-separated list of scanners: vuln,secret,config,license (default: vuln)"
    )
    parser.add_argument(
        "--min-severity",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"],
        default="MEDIUM",
        help="Minimum severity level to report (default: MEDIUM)"
    )
    parser.add_argument(
        "--skip-db-update",
        action="store_true",
        help="Skip vulnerability database update"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Perform offline scan"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Scan timeout in seconds (default: 600)"
    )
    
    # SBOM options
    parser.add_argument(
        "--sbom",
        action="store_true",
        help="Generate SBOM instead of scanning for vulnerabilities"
    )
    parser.add_argument(
        "--sbom-format",
        choices=["cyclonedx", "spdx", "spdx-json"],
        default="cyclonedx",
        help="SBOM format (default: cyclonedx)"
    )
    parser.add_argument(
        "--sbom-output",
        help="Output file for SBOM (default: stdout)"
    )
    
    # GitLab options
    parser.add_argument(
        "--project",
        help="GitLab project (namespace/project) - required for creating issues"
    )
    parser.add_argument(
        "--token",
        help="GitLab personal access token (or set GITLAB_TOKEN env var)"
    )
    parser.add_argument(
        "--gitlab-url",
        default=os.getenv("GITLAB_URL", "https://gitlab.com"),
        help="GitLab instance URL (default: https://gitlab.com)"
    )
    parser.add_argument(
        "--group-by-severity",
        action="store_true",
        help="Group findings by severity (one issue per severity level)"
    )
    
    # Output options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview findings without creating GitLab issues"
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=10,
        help="Maximum number of findings to display in detail (default: 10)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    # Print banner
    if not args.quiet:
        print_banner()
    
    # Handle SBOM generation
    if args.sbom:
        try:
            scanner = TrivyScanner()
            target = args.image or args.directory
            
            print(f"Generating SBOM for: {target}")
            print(f"Format: {args.sbom_format}")
            print()
            
            sbom = scanner.generate_sbom(
                target,
                output_format=args.sbom_format,
                output_file=args.sbom_output
            )
            
            if not args.sbom_output:
                print(sbom)
            else:
                print(f"✅ SBOM saved to: {args.sbom_output}")
            
            return
            
        except TrivyScannerError as e:
            print(f"❌ SBOM generation failed: {e}")
            sys.exit(1)
    
    # Initialize scanner
    try:
        scanner = TrivyScanner(
            min_severity=TrivySeverity(args.min_severity),
            timeout=args.timeout,
            skip_db_update=args.skip_db_update,
            offline_scan=args.offline,
        )
    except TrivyNotInstalledError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Perform scan
    try:
        scanners_list = [s.strip() for s in args.scanners.split(",")]
        
        if args.image:
            print(f"Scanning container image: {args.image}")
            print(f"Scanners: {', '.join(scanners_list)}")
            print(f"Min severity: {args.min_severity}")
            print()
            scan_result = scanner.scan_image(args.image, scanners=scanners_list)
        
        elif args.directory:
            print(f"Scanning filesystem: {args.directory}")
            print(f"Scanners: {', '.join(scanners_list)}")
            print(f"Min severity: {args.min_severity}")
            print()
            scan_result = scanner.scan_filesystem(args.directory, scanners=scanners_list)
        
        elif args.repository:
            print(f"Scanning repository: {args.repository}")
            print(f"Scanners: {', '.join(scanners_list)}")
            print(f"Min severity: {args.min_severity}")
            print()
            scan_result = scanner.scan_repository(args.repository, scanners=scanners_list)
        
    except TrivyScannerError as e:
        print(f"❌ Scan failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Print results
    if not args.quiet:
        print_scan_summary(scan_result)
        print_findings_detail(scan_result, max_findings=args.max_findings)
    
    # Create GitLab issues
    if args.project and scan_result.has_findings:
        if args.dry_run:
            print(f"\n{'=' * 70}")
            print("DRY-RUN MODE - Issues would be created:")
            print("=" * 70)
            
            issues = scanner.scan_result_to_issues(
                scan_result,
                args.project,
                group_by_severity=args.group_by_severity
            )
            
            for i, issue in enumerate(issues, 1):
                print(f"\n{i}. {issue.title}")
                print(f"   Labels: {', '.join(issue.labels)}")
                print(f"   Confidential: {issue.confidential}")
            
            print(f"\n{'=' * 70}")
            print(f"Would create {len(issues)} issue(s)")
            print("=" * 70)
        else:
            # Get GitLab token from environment or args
            # Priority: --token argument > GITLAB_TOKEN env var
            token = args.token or os.getenv("GITLAB_TOKEN")
            if not token:
                print("❌ GitLab token required. Use --token or set GITLAB_TOKEN env var")
                print("   Get project token from: Project Settings > Access Tokens")
                sys.exit(1)
            
            create_gitlab_issues(
                scan_result,
                args.project,
                args.gitlab_url,
                token,
                group_by_severity=args.group_by_severity
            )
    
    elif args.project and not scan_result.has_findings:
        print("\n✅ No security issues found - no issues to create")
    
    # Exit with appropriate code
    if scan_result.critical_count > 0 or scan_result.high_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
