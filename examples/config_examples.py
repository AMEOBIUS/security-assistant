"""
Configuration Examples for Security Assistant.

This module demonstrates various configuration scenarios
and best practices.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.config import (
    BanditConfig,
    DeduplicationStrategy,
    GitLabConfig,
    OrchestratorConfig,
    ReportConfig,
    ReportFormat,
    SecurityAssistantConfig,
    SemgrepConfig,
    ThresholdConfig,
    TrivyConfig,
)


def example_minimal_config():
    """Example: Minimal configuration with defaults."""
    print("=" * 60)
    print("Minimal Configuration Example")
    print("=" * 60)
    
    config = SecurityAssistantConfig()
    
    print("\nDefault configuration:")
    print(f"  Bandit enabled: {config.bandit.enabled}")
    print(f"  Semgrep enabled: {config.semgrep.enabled}")
    print(f"  Trivy enabled: {config.trivy.enabled}")
    print(f"  Dedup strategy: {config.orchestrator.deduplication_strategy.value}")
    print(f"  Max workers: {config.orchestrator.max_workers}")
    print(f"  Output dir: {config.report.output_dir}")
    
    # Save to file
    config.save('config/minimal.yaml', format='yaml')
    print("\n✅ Saved to: config/minimal.yaml")


def example_python_only_config():
    """Example: Python-only scanning configuration."""
    print("\n" + "=" * 60)
    print("Python-Only Configuration Example")
    print("=" * 60)
    
    config = SecurityAssistantConfig(
        bandit=BanditConfig(
            enabled=True,
            severity_level='low',
            confidence_level='medium',
            exclude_dirs=['tests', 'test', '.venv', 'venv']
        ),
        semgrep=SemgrepConfig(
            enabled=True,
            rules=['p/python', 'p/security-audit']
        ),
        trivy=TrivyConfig(
            enabled=False  # Disable Trivy for Python-only
        ),
        orchestrator=OrchestratorConfig(
            deduplication_strategy=DeduplicationStrategy.BOTH,
            max_workers=2
        ),
        report=ReportConfig(
            formats=[ReportFormat.JSON, ReportFormat.HTML],
            output_dir='python-security-reports'
        ),
        scan_target='src/'
    )
    
    print("\nPython-only configuration:")
    print(f"  Bandit: {config.bandit.enabled}")
    print(f"  Semgrep: {config.semgrep.enabled} (rules: {config.semgrep.rules})")
    print(f"  Trivy: {config.trivy.enabled}")
    print(f"  Scan target: {config.scan_target}")
    
    config.save('config/python-only.yaml', format='yaml')
    print("\n✅ Saved to: config/python-only.yaml")


def example_strict_security_config():
    """Example: Strict security configuration for production."""
    print("\n" + "=" * 60)
    print("Strict Security Configuration Example")
    print("=" * 60)
    
    config = SecurityAssistantConfig(
        bandit=BanditConfig(
            enabled=True,
            severity_level='low',  # Catch everything
            confidence_level='low',
            skip_tests=[]  # Don't skip any tests
        ),
        semgrep=SemgrepConfig(
            enabled=True,
            rules=[
                'p/security-audit',
                'p/owasp-top-ten',
                'p/cwe-top-25'
            ],
            max_memory=8000
        ),
        trivy=TrivyConfig(
            enabled=True,
            severity=['CRITICAL', 'HIGH'],  # Only critical and high
            scanners=['vuln', 'secret', 'config']
        ),
        orchestrator=OrchestratorConfig(
            deduplication_strategy=DeduplicationStrategy.BOTH,
            max_workers=4,
            continue_on_error=False  # Fail fast
        ),
        report=ReportConfig(
            formats=[ReportFormat.JSON, ReportFormat.HTML, ReportFormat.SARIF],
            output_dir='security-reports',
            include_code_snippets=True
        ),
        thresholds=ThresholdConfig(
            fail_on_critical=True,
            fail_on_high=True,
            fail_on_medium=False,
            max_critical=0,
            max_high=0  # Zero tolerance for critical and high
        ),
        verbose=True,
        log_level='DEBUG'
    )
    
    print("\nStrict security configuration:")
    print("  All scanners enabled: ✓")
    print(f"  Fail on critical: {config.thresholds.fail_on_critical}")
    print(f"  Fail on high: {config.thresholds.fail_on_high}")
    print(f"  Max critical: {config.thresholds.max_critical}")
    print(f"  Max high: {config.thresholds.max_high}")
    print(f"  Continue on error: {config.orchestrator.continue_on_error}")
    
    config.save('config/strict-security.yaml', format='yaml')
    print("\n✅ Saved to: config/strict-security.yaml")


def example_gitlab_integration_config():
    """Example: Configuration with GitLab integration."""
    print("\n" + "=" * 60)
    print("GitLab Integration Configuration Example")
    print("=" * 60)
    
    config = SecurityAssistantConfig(
        bandit=BanditConfig(enabled=True),
        semgrep=SemgrepConfig(enabled=True),
        trivy=TrivyConfig(enabled=True),
        orchestrator=OrchestratorConfig(
            deduplication_strategy=DeduplicationStrategy.BOTH,
            max_workers=3
        ),
        report=ReportConfig(
            formats=[ReportFormat.JSON, ReportFormat.HTML, ReportFormat.MARKDOWN],
            output_dir='security-reports'
        ),
        gitlab=GitLabConfig(
            enabled=True,
            url='https://gitlab.com',
            # token and project_id should be set via environment variables
            create_issues=True,
            priority_threshold=75,
            max_issues=10,
            issue_labels=['security', 'automated', 'high-priority'],
            assignee_ids=[]
        ),
        thresholds=ThresholdConfig(
            fail_on_critical=True,
            fail_on_high=False
        )
    )
    
    print("\nGitLab integration configuration:")
    print(f"  GitLab enabled: {config.gitlab.enabled}")
    print(f"  Create issues: {config.gitlab.create_issues}")
    print(f"  Priority threshold: {config.gitlab.priority_threshold}")
    print(f"  Max issues: {config.gitlab.max_issues}")
    print(f"  Issue labels: {config.gitlab.issue_labels}")
    
    config.save('config/gitlab-integration.yaml', format='yaml')
    print("\n✅ Saved to: config/gitlab-integration.yaml")
    print("\nNote: Set these environment variables:")
    print("  export SA_GITLAB_TOKEN='your-token'")
    print("  export SA_GITLAB_PROJECT_ID='namespace/project'")


def example_quick_scan_config():
    """Example: Quick scan configuration for development."""
    print("\n" + "=" * 60)
    print("Quick Scan Configuration Example")
    print("=" * 60)
    
    config = SecurityAssistantConfig(
        bandit=BanditConfig(
            enabled=True,
            severity_level='high',  # Only high severity
            confidence_level='high'
        ),
        semgrep=SemgrepConfig(
            enabled=False  # Disable for speed
        ),
        trivy=TrivyConfig(
            enabled=False  # Disable for speed
        ),
        orchestrator=OrchestratorConfig(
            deduplication_strategy=DeduplicationStrategy.LOCATION,
            max_workers=1  # Single worker for simplicity
        ),
        report=ReportConfig(
            formats=[ReportFormat.JSON],  # JSON only
            output_dir='quick-scan-reports'
        ),
        thresholds=ThresholdConfig(
            fail_on_critical=True,
            fail_on_high=False,
            fail_on_medium=False
        ),
        verbose=False
    )
    
    print("\nQuick scan configuration:")
    print("  Bandit only: ✓")
    print(f"  Severity: {config.bandit.severity_level}")
    print(f"  Workers: {config.orchestrator.max_workers}")
    print(f"  Report format: {[f.value for f in config.report.formats]}")
    
    config.save('config/quick-scan.yaml', format='yaml')
    print("\n✅ Saved to: config/quick-scan.yaml")


def example_config_merging():
    """Example: Configuration merging from multiple sources."""
    print("\n" + "=" * 60)
    print("Configuration Merging Example")
    print("=" * 60)
    
    # Base configuration
    base_config = SecurityAssistantConfig(
        bandit=BanditConfig(enabled=True),
        semgrep=SemgrepConfig(enabled=True),
        trivy=TrivyConfig(enabled=True)
    )
    
    print("\nBase configuration:")
    print(f"  Bandit: {base_config.bandit.enabled}")
    print(f"  Semgrep: {base_config.semgrep.enabled}")
    print(f"  Trivy: {base_config.trivy.enabled}")
    print(f"  Max workers: {base_config.orchestrator.max_workers}")
    
    # Override configuration
    override_config = SecurityAssistantConfig(
        trivy=TrivyConfig(enabled=False),  # Disable Trivy
        orchestrator=OrchestratorConfig(max_workers=8)  # Increase workers
    )
    
    print("\nOverride configuration:")
    print(f"  Trivy: {override_config.trivy.enabled}")
    print(f"  Max workers: {override_config.orchestrator.max_workers}")
    
    # Merge configurations
    merged_config = base_config.merge(override_config)
    
    print("\nMerged configuration:")
    print(f"  Bandit: {merged_config.bandit.enabled}")
    print(f"  Semgrep: {merged_config.semgrep.enabled}")
    print(f"  Trivy: {merged_config.trivy.enabled}")
    print(f"  Max workers: {merged_config.orchestrator.max_workers}")
    
    print("\n✅ Configuration merged successfully")


def example_config_validation():
    """Example: Configuration validation."""
    print("\n" + "=" * 60)
    print("Configuration Validation Example")
    print("=" * 60)
    
    # Valid configuration
    valid_config = SecurityAssistantConfig(
        bandit=BanditConfig(enabled=True),
        gitlab=GitLabConfig(
            enabled=True,
            url='https://gitlab.com',
            token='dummy-token',
            project_id='namespace/project',
            create_issues=True
        )
    )
    
    errors = valid_config.validate()
    print("\nValid configuration:")
    if errors:
        print("  Errors found:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✅ No errors")
    
    # Invalid configuration
    invalid_config = SecurityAssistantConfig(
        bandit=BanditConfig(enabled=False),
        semgrep=SemgrepConfig(enabled=False),
        trivy=TrivyConfig(enabled=False),  # No scanners enabled
        orchestrator=OrchestratorConfig(max_workers=0),  # Invalid
        gitlab=GitLabConfig(
            enabled=True,
            create_issues=True
            # Missing required fields
        )
    )
    
    errors = invalid_config.validate()
    print("\nInvalid configuration:")
    if errors:
        print("  ❌ Errors found:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  No errors")


def main():
    """Run all configuration examples."""
    print("\n" + "=" * 60)
    print("Security Assistant - Configuration Examples")
    print("=" * 60 + "\n")
    
    # Create config directory
    Path('config').mkdir(exist_ok=True)
    
    examples = [
        example_minimal_config,
        example_python_only_config,
        example_strict_security_config,
        example_gitlab_integration_config,
        example_quick_scan_config,
        example_config_merging,
        example_config_validation
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
