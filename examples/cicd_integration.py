"""
CI/CD Integration Examples for Security Assistant.

This module demonstrates how to integrate Security Assistant
into various CI/CD pipelines programmatically.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.scanners.bandit_scanner import BanditScanner
from security_assistant.scanners.semgrep_scanner import SemgrepScanner
from security_assistant.scanners.trivy_scanner import TrivyScanner
from security_assistant.config import load_config


def example_gitlab_ci() -> int:
    """
    Example: GitLab CI/CD integration.
    
    This function demonstrates how to use Security Assistant
    in a GitLab CI/CD pipeline with environment variables.
    
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 60)
    print("GitLab CI/CD Integration Example")
    print("=" * 60)
    
    # Load configuration from environment variables
    config = load_config(use_env=True)
    
    # Create orchestrator
    orchestrator = ScanOrchestrator(
        deduplication_strategy=config.orchestrator.deduplication_strategy.value,
        max_workers=config.orchestrator.max_workers
    )
    
    # Enable scanners based on config
    if config.bandit.enabled:
        print("✓ Enabling Bandit")
        orchestrator.enable_scanner('bandit', BanditScanner())
    
    if config.semgrep.enabled:
        print("✓ Enabling Semgrep")
        orchestrator.enable_scanner('semgrep', SemgrepScanner())
    
    if config.trivy.enabled:
        print("✓ Enabling Trivy")
        orchestrator.enable_scanner('trivy', TrivyScanner())
    
    # Run scan
    print(f"\n🔍 Scanning: {config.scan_target}")
    result = orchestrator.scan_directory(config.scan_target)
    
    # Save results
    output_dir = Path(config.report.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / 'scan-results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'total_findings': len(result.all_findings),
            'deduplicated_findings': len(result.deduplicated_findings),
            'execution_time': result.execution_time_seconds,
            'findings_by_severity': result.findings_by_severity,
            'findings_by_scanner': result.findings_by_scanner
        }, f, indent=2)
    
    # Print summary
    print(f"\n✅ Scan complete!")
    print(f"Total findings: {len(result.deduplicated_findings)}")
    print(f"Execution time: {result.execution_time_seconds:.2f}s")
    print(f"\nFindings by severity:")
    for severity, count in sorted(result.findings_by_severity.items()):
        print(f"  {severity}: {count}")
    
    # Check thresholds
    critical_count = result.findings_by_severity.get('CRITICAL', 0)
    high_count = result.findings_by_severity.get('HIGH', 0)
    
    if config.thresholds.fail_on_critical and critical_count > 0:
        print(f"\n❌ Pipeline failed: {critical_count} critical findings")
        return 1
    
    if config.thresholds.fail_on_high and high_count > 0:
        print(f"\n❌ Pipeline failed: {high_count} high findings")
        return 1
    
    print("\n✅ No blocking findings")
    return 0


def example_github_actions() -> Dict[str, Any]:
    """
    Example: GitHub Actions integration.
    
    This function demonstrates how to use Security Assistant
    in GitHub Actions with SARIF output.
    
    Returns:
        Dictionary with scan results and SARIF data
    """
    print("=" * 60)
    print("GitHub Actions Integration Example")
    print("=" * 60)
    
    # Load config
    config = load_config(use_env=True)
    
    # Create orchestrator
    orchestrator = ScanOrchestrator(
        deduplication_strategy='both',
        max_workers=3
    )
    
    # Enable all scanners
    orchestrator.enable_scanner('bandit', BanditScanner())
    orchestrator.enable_scanner('semgrep', SemgrepScanner())
    orchestrator.enable_scanner('trivy', TrivyScanner())
    
    # Run scan
    print(f"\n🔍 Scanning: {config.scan_target}")
    result = orchestrator.scan_directory(config.scan_target)
    
    # Generate SARIF report
    sarif_runs = []
    
    findings_by_scanner = {}
    for finding in result.deduplicated_findings:
        scanner = finding.scanner
        if scanner not in findings_by_scanner:
            findings_by_scanner[scanner] = []
        findings_by_scanner[scanner].append(finding)
    
    for scanner, findings in findings_by_scanner.items():
        sarif_results = []
        
        for finding in findings:
            severity_map = {
                'CRITICAL': 'error',
                'HIGH': 'error',
                'MEDIUM': 'warning',
                'LOW': 'note',
                'INFO': 'note'
            }
            
            sarif_result = {
                'ruleId': finding.finding_id,
                'level': severity_map.get(finding.severity.value, 'warning'),
                'message': {'text': finding.title},
                'locations': [{
                    'physicalLocation': {
                        'artifactLocation': {'uri': finding.file_path},
                        'region': {
                            'startLine': finding.line_start,
                            'endLine': finding.line_end
                        }
                    }
                }]
            }
            sarif_results.append(sarif_result)
        
        sarif_run = {
            'tool': {
                'driver': {
                    'name': scanner.capitalize(),
                    'version': '1.0.0'
                }
            },
            'results': sarif_results
        }
        sarif_runs.append(sarif_run)
    
    sarif_report = {
        'version': '2.1.0',
        '$schema': 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
        'runs': sarif_runs
    }
    
    # Save SARIF
    output_dir = Path('security-reports')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'results.sarif', 'w') as f:
        json.dump(sarif_report, f, indent=2)
    
    print(f"\n✅ SARIF report generated")
    print(f"Total findings: {len(result.deduplicated_findings)}")
    
    return {
        'total_findings': len(result.deduplicated_findings),
        'findings_by_severity': result.findings_by_severity,
        'sarif': sarif_report
    }


def example_jenkins() -> None:
    """
    Example: Jenkins integration.
    
    This function demonstrates how to use Security Assistant
    in Jenkins with HTML report generation.
    """
    print("=" * 60)
    print("Jenkins Integration Example")
    print("=" * 60)
    
    # Load config from file
    config_file = Path('security-assistant.yaml')
    if config_file.exists():
        config = load_config(config_file=config_file)
    else:
        config = load_config(use_env=True)
    
    # Create orchestrator
    orchestrator = ScanOrchestrator(
        deduplication_strategy=config.orchestrator.deduplication_strategy.value,
        max_workers=config.orchestrator.max_workers
    )
    
    # Enable scanners
    enabled = []
    if config.bandit.enabled:
        orchestrator.enable_scanner('bandit', BanditScanner())
        enabled.append('Bandit')
    if config.semgrep.enabled:
        orchestrator.enable_scanner('semgrep', SemgrepScanner())
        enabled.append('Semgrep')
    if config.trivy.enabled:
        orchestrator.enable_scanner('trivy', TrivyScanner())
        enabled.append('Trivy')
    
    print(f"\nEnabled scanners: {', '.join(enabled)}")
    
    # Run scan
    print(f"🔍 Scanning: {config.scan_target}")
    result = orchestrator.scan_directory(config.scan_target)
    
    # Save results
    output_dir = Path(config.report.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON results
    with open(output_dir / 'scan-results.json', 'w') as f:
        json.dump({
            'total_findings': len(result.all_findings),
            'deduplicated_findings': len(result.deduplicated_findings),
            'execution_time': result.execution_time_seconds,
            'findings_by_severity': result.findings_by_severity,
            'findings_by_scanner': result.findings_by_scanner,
            'findings': [
                {
                    'id': f.finding_id,
                    'severity': f.severity.value,
                    'title': f.title,
                    'file': f.file_path,
                    'line': f.line_start,
                    'priority': f.priority_score
                }
                for f in result.deduplicated_findings
            ]
        }, f, indent=2)
    
    print(f"\n✅ Results saved to {output_dir}")
    print(f"Total findings: {len(result.deduplicated_findings)}")
    print(f"Execution time: {result.execution_time_seconds:.2f}s")


def example_custom_pipeline() -> None:
    """
    Example: Custom pipeline integration.
    
    This function demonstrates advanced usage with custom
    configuration and error handling.
    """
    print("=" * 60)
    print("Custom Pipeline Integration Example")
    print("=" * 60)
    
    try:
        # Create custom configuration
        from security_assistant.config import (
            SecurityAssistantConfig,
            BanditConfig,
            SemgrepConfig,
            OrchestratorConfig,
            ThresholdConfig
        )
        
        config = SecurityAssistantConfig(
            bandit=BanditConfig(
                enabled=True,
                severity_level='medium',
                confidence_level='medium'
            ),
            semgrep=SemgrepConfig(
                enabled=True,
                rules=['p/security-audit', 'p/owasp-top-ten']
            ),
            orchestrator=OrchestratorConfig(
                deduplication_strategy='both',
                max_workers=4,
                continue_on_error=True
            ),
            thresholds=ThresholdConfig(
                fail_on_critical=True,
                fail_on_high=True,
                max_critical=0,
                max_high=5
            ),
            scan_target='src/'
        )
        
        # Validate config
        errors = config.validate()
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return
        
        # Create orchestrator
        orchestrator = ScanOrchestrator(
            deduplication_strategy=config.orchestrator.deduplication_strategy.value,
            max_workers=config.orchestrator.max_workers
        )
        
        # Enable scanners
        orchestrator.enable_scanner('bandit', BanditScanner())
        orchestrator.enable_scanner('semgrep', SemgrepScanner())
        
        # Run scan with error handling
        print(f"\n🔍 Scanning: {config.scan_target}")
        result = orchestrator.scan_directory(config.scan_target)
        
        # Analyze results
        critical = result.findings_by_severity.get('CRITICAL', 0)
        high = result.findings_by_severity.get('HIGH', 0)
        
        print(f"\n📊 Scan Results:")
        print(f"  Total findings: {len(result.deduplicated_findings)}")
        print(f"  Critical: {critical}")
        print(f"  High: {high}")
        print(f"  Execution time: {result.execution_time_seconds:.2f}s")
        
        # Check thresholds
        if critical > config.thresholds.max_critical:
            print(f"\n❌ Failed: {critical} critical findings (max: {config.thresholds.max_critical})")
            sys.exit(1)
        
        if high > config.thresholds.max_high:
            print(f"\n❌ Failed: {high} high findings (max: {config.thresholds.max_high})")
            sys.exit(1)
        
        print("\n✅ Pipeline passed all checks")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Security Assistant - CI/CD Integration Examples")
    print("=" * 60 + "\n")
    
    examples = [
        ("GitLab CI/CD", example_gitlab_ci),
        ("GitHub Actions", example_github_actions),
        ("Jenkins", example_jenkins),
        ("Custom Pipeline", example_custom_pipeline)
    ]
    
    for name, func in examples:
        print(f"\n{'=' * 60}")
        print(f"Running: {name}")
        print('=' * 60)
        
        try:
            result = func()
            if isinstance(result, int):
                print(f"\nExit code: {result}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print()


if __name__ == '__main__':
    main()
