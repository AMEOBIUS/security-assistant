"""
Configuration management for Security Assistant.

This module provides centralized configuration management with support for:
- YAML/JSON configuration files
- Environment variables
- Command-line arguments
- Default values
- Validation
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

try:
    import yaml
except ImportError:
    yaml = None

try:
    from .security_validator import ConfigurationSandbox
except ImportError:
    ConfigurationSandbox = None


class DeduplicationStrategy(str, Enum):
    """Deduplication strategies."""
    LOCATION = "location"
    CONTENT = "content"
    BOTH = "both"


class ReportFormat(str, Enum):
    """Report output formats."""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    SARIF = "sarif"
    TEXT = "text"


@dataclass
class ScannerConfig:
    """Configuration for individual scanners."""
    enabled: bool = True
    config_file: Optional[str] = None
    extra_args: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BanditConfig(ScannerConfig):
    """Bandit-specific configuration."""
    severity_level: str = "low"  # low, medium, high
    confidence_level: str = "low"  # low, medium, high
    exclude_dirs: List[str] = field(default_factory=lambda: [
        "tests", "test", ".git", ".venv", "venv", "node_modules"
    ])
    skip_tests: List[str] = field(default_factory=list)


@dataclass
class SemgrepConfig(ScannerConfig):
    """Semgrep-specific configuration."""
    rules: List[str] = field(default_factory=lambda: ["auto"])
    exclude_rules: List[str] = field(default_factory=list)
    max_memory: int = 5000  # MB
    max_target_bytes: int = 1000000  # 1MB


@dataclass
class TrivyConfig(ScannerConfig):
    """Trivy-specific configuration."""
    severity: List[str] = field(default_factory=lambda: [
        "CRITICAL", "HIGH", "MEDIUM", "LOW"
    ])
    scanners: List[str] = field(default_factory=lambda: ["vuln", "secret", "config"])
    skip_dirs: List[str] = field(default_factory=lambda: [
        ".git", ".venv", "venv", "node_modules"
    ])


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""
    deduplication_strategy: DeduplicationStrategy = DeduplicationStrategy.BOTH
    max_workers: int = 3
    parallel_execution: bool = True
    continue_on_error: bool = True


@dataclass
class ReportConfig:
    """Report generation configuration."""
    formats: List[ReportFormat] = field(default_factory=lambda: [
        ReportFormat.JSON, ReportFormat.HTML
    ])
    output_dir: str = "security-reports"
    include_code_snippets: bool = True
    max_snippet_lines: int = 10
    group_by: str = "severity"  # severity, scanner, file


@dataclass
class GitLabConfig:
    """GitLab integration configuration."""
    enabled: bool = False
    url: Optional[str] = None
    token: Optional[str] = None
    project_id: Optional[str] = None
    create_issues: bool = False
    priority_threshold: int = 70
    max_issues: int = 10
    issue_labels: List[str] = field(default_factory=lambda: ["security"])
    assignee_ids: List[int] = field(default_factory=list)


@dataclass
class ThresholdConfig:
    """Severity threshold configuration."""
    fail_on_critical: bool = True
    fail_on_high: bool = False
    fail_on_medium: bool = False
    max_critical: int = 0
    max_high: int = 10
    max_medium: int = 50


@dataclass
class SecurityAssistantConfig:
    """Main configuration for Security Assistant."""
    
    # Scanner configurations
    bandit: BanditConfig = field(default_factory=BanditConfig)
    semgrep: SemgrepConfig = field(default_factory=SemgrepConfig)
    trivy: TrivyConfig = field(default_factory=TrivyConfig)
    
    # Orchestrator configuration
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    
    # Report configuration
    report: ReportConfig = field(default_factory=ReportConfig)
    
    # GitLab integration
    gitlab: GitLabConfig = field(default_factory=GitLabConfig)
    
    # Thresholds
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    
    # General settings
    scan_target: str = "."
    verbose: bool = False
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'bandit': self.bandit.to_dict(),
            'semgrep': self.semgrep.to_dict(),
            'trivy': self.trivy.to_dict(),
            'orchestrator': asdict(self.orchestrator),
            'report': asdict(self.report),
            'gitlab': asdict(self.gitlab),
            'thresholds': asdict(self.thresholds),
            'scan_target': self.scan_target,
            'verbose': self.verbose,
            'log_level': self.log_level,
            'log_file': self.log_file
        }
    
    def save(self, path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Save configuration to file.
        
        Args:
            path: Output file path
            format: File format ('yaml' or 'json')
        """
        path = Path(path)
        data = self.to_dict()
        
        with open(path, 'w') as f:
            if format == 'yaml':
                if yaml is None:
                    raise ImportError("PyYAML is required for YAML format. Install with: pip install pyyaml")
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif format == 'json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityAssistantConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            SecurityAssistantConfig instance
        """
        config = cls()
        
        # Update scanner configs
        if 'bandit' in data:
            config.bandit = BanditConfig(**data['bandit'])
        if 'semgrep' in data:
            config.semgrep = SemgrepConfig(**data['semgrep'])
        if 'trivy' in data:
            config.trivy = TrivyConfig(**data['trivy'])
        
        # Update orchestrator config
        if 'orchestrator' in data:
            orch_data = data['orchestrator']
            if 'deduplication_strategy' in orch_data:
                orch_data['deduplication_strategy'] = DeduplicationStrategy(
                    orch_data['deduplication_strategy']
                )
            config.orchestrator = OrchestratorConfig(**orch_data)
        
        # Update report config
        if 'report' in data:
            report_data = data['report']
            if 'formats' in report_data:
                report_data['formats'] = [
                    ReportFormat(f) for f in report_data['formats']
                ]
            config.report = ReportConfig(**report_data)
        
        # Update GitLab config
        if 'gitlab' in data:
            config.gitlab = GitLabConfig(**data['gitlab'])
        
        # Update thresholds
        if 'thresholds' in data:
            config.thresholds = ThresholdConfig(**data['thresholds'])
        
        # Update general settings
        if 'scan_target' in data:
            config.scan_target = data['scan_target']
        if 'verbose' in data:
            config.verbose = data['verbose']
        if 'log_level' in data:
            config.log_level = data['log_level']
        if 'log_file' in data:
            config.log_file = data['log_file']
        
        return config
    
    @classmethod
    def load(cls, path: Union[str, Path], validate_security: bool = True) -> 'SecurityAssistantConfig':
        """
        Load configuration from file.
        
        Args:
            path: Configuration file path
            validate_security: Enable security validation (default: True)
            
        Returns:
            SecurityAssistantConfig instance
            
        Raises:
            ValueError: If security validation fails
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        # META-SECURITY: Validate config file path
        if validate_security and ConfigurationSandbox is not None:
            sandbox = ConfigurationSandbox(project_root=Path.cwd())
            validation_result = sandbox.validate_config_path(path)
            
            if not validation_result.is_valid:
                error_msg = (
                    f"Configuration file validation failed:\n"
                    + "\n".join(f"  - {err}" for err in validation_result.errors)
                )
                raise ValueError(error_msg)
            
            # Log warnings
            import logging
            logger = logging.getLogger(__name__)
            for warning in validation_result.warnings:
                logger.warning(f"⚠️  Config validation warning: {warning}")
        
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                if yaml is None:
                    raise ImportError("PyYAML is required for YAML format. Install with: pip install pyyaml")
                data = yaml.safe_load(f)
            elif path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return cls.from_dict(data)
    
    @classmethod
    def from_env(cls) -> 'SecurityAssistantConfig':
        """
        Create configuration from environment variables.
        
        Environment variables:
        - SA_BANDIT_ENABLED: Enable Bandit scanner
        - SA_SEMGREP_ENABLED: Enable Semgrep scanner
        - SA_TRIVY_ENABLED: Enable Trivy scanner
        - SA_DEDUP_STRATEGY: Deduplication strategy
        - SA_MAX_WORKERS: Maximum parallel workers
        - SA_REPORT_FORMATS: Comma-separated report formats
        - SA_OUTPUT_DIR: Report output directory
        - SA_GITLAB_URL: GitLab URL
        - SA_GITLAB_TOKEN: GitLab API token
        - SA_GITLAB_PROJECT_ID: GitLab project ID
        - SA_FAIL_ON_CRITICAL: Fail on critical findings
        - SA_FAIL_ON_HIGH: Fail on high findings
        - SA_SCAN_TARGET: Scan target directory
        - SA_VERBOSE: Verbose output
        - SA_LOG_LEVEL: Log level
        
        Returns:
            SecurityAssistantConfig instance
        """
        config = cls()
        
        # Scanner enablement
        if os.getenv('SA_BANDIT_ENABLED'):
            config.bandit.enabled = os.getenv('SA_BANDIT_ENABLED').lower() == 'true'
        if os.getenv('SA_SEMGREP_ENABLED'):
            config.semgrep.enabled = os.getenv('SA_SEMGREP_ENABLED').lower() == 'true'
        if os.getenv('SA_TRIVY_ENABLED'):
            config.trivy.enabled = os.getenv('SA_TRIVY_ENABLED').lower() == 'true'
        
        # Orchestrator
        if os.getenv('SA_DEDUP_STRATEGY'):
            config.orchestrator.deduplication_strategy = DeduplicationStrategy(
                os.getenv('SA_DEDUP_STRATEGY')
            )
        if os.getenv('SA_MAX_WORKERS'):
            config.orchestrator.max_workers = int(os.getenv('SA_MAX_WORKERS'))
        
        # Report
        if os.getenv('SA_REPORT_FORMATS'):
            formats = os.getenv('SA_REPORT_FORMATS').split(',')
            config.report.formats = [ReportFormat(f.strip()) for f in formats]
        if os.getenv('SA_OUTPUT_DIR'):
            config.report.output_dir = os.getenv('SA_OUTPUT_DIR')
        
        # GitLab
        if os.getenv('SA_GITLAB_URL'):
            config.gitlab.enabled = True
            config.gitlab.url = os.getenv('SA_GITLAB_URL')
        if os.getenv('SA_GITLAB_TOKEN'):
            config.gitlab.token = os.getenv('SA_GITLAB_TOKEN')
        if os.getenv('SA_GITLAB_PROJECT_ID'):
            config.gitlab.project_id = os.getenv('SA_GITLAB_PROJECT_ID')
        if os.getenv('SA_GITLAB_CREATE_ISSUES'):
            config.gitlab.create_issues = os.getenv('SA_GITLAB_CREATE_ISSUES').lower() == 'true'
        if os.getenv('SA_PRIORITY_THRESHOLD'):
            config.gitlab.priority_threshold = int(os.getenv('SA_PRIORITY_THRESHOLD'))
        
        # Thresholds
        if os.getenv('SA_FAIL_ON_CRITICAL'):
            config.thresholds.fail_on_critical = os.getenv('SA_FAIL_ON_CRITICAL').lower() == 'true'
        if os.getenv('SA_FAIL_ON_HIGH'):
            config.thresholds.fail_on_high = os.getenv('SA_FAIL_ON_HIGH').lower() == 'true'
        if os.getenv('SA_FAIL_ON_MEDIUM'):
            config.thresholds.fail_on_medium = os.getenv('SA_FAIL_ON_MEDIUM').lower() == 'true'
        
        # General
        if os.getenv('SA_SCAN_TARGET'):
            config.scan_target = os.getenv('SA_SCAN_TARGET')
        if os.getenv('SA_VERBOSE'):
            config.verbose = os.getenv('SA_VERBOSE').lower() == 'true'
        if os.getenv('SA_LOG_LEVEL'):
            config.log_level = os.getenv('SA_LOG_LEVEL')
        if os.getenv('SA_LOG_FILE'):
            config.log_file = os.getenv('SA_LOG_FILE')
        
        return config
    
    def merge(self, other: 'SecurityAssistantConfig') -> 'SecurityAssistantConfig':
        """
        Merge with another configuration (other takes precedence).
        
        Args:
            other: Configuration to merge
            
        Returns:
            New merged configuration
        """
        merged_dict = self.to_dict()
        other_dict = other.to_dict()
        
        def deep_merge(base: Dict, override: Dict) -> Dict:
            """Deep merge two dictionaries."""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        merged = deep_merge(merged_dict, other_dict)
        return self.from_dict(merged)
    
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check at least one scanner is enabled
        if not any([self.bandit.enabled, self.semgrep.enabled, self.trivy.enabled]):
            errors.append("At least one scanner must be enabled")
        
        # Check max_workers
        if self.orchestrator.max_workers < 1:
            errors.append("max_workers must be at least 1")
        
        # Check output directory
        if not self.report.output_dir:
            errors.append("output_dir cannot be empty")
        
        # Check GitLab config if enabled
        if self.gitlab.enabled:
            if not self.gitlab.url:
                errors.append("GitLab URL is required when GitLab is enabled")
            if self.gitlab.create_issues and not self.gitlab.token:
                errors.append("GitLab token is required for issue creation")
            if self.gitlab.create_issues and not self.gitlab.project_id:
                errors.append("GitLab project_id is required for issue creation")
        
        # Check priority threshold
        if not 0 <= self.gitlab.priority_threshold <= 100:
            errors.append("priority_threshold must be between 0 and 100")
        
        # Check log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            errors.append(f"log_level must be one of {valid_log_levels}")
        
        return errors


class ConfigManager:
    """Configuration manager with multiple sources."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self._config: Optional[SecurityAssistantConfig] = None
    
    def load_config(
        self,
        config_file: Optional[Union[str, Path]] = None,
        use_env: bool = True,
        defaults: Optional[SecurityAssistantConfig] = None
    ) -> SecurityAssistantConfig:
        """
        Load configuration from multiple sources.
        
        Priority (highest to lowest):
        1. Environment variables
        2. Configuration file
        3. Defaults
        
        Args:
            config_file: Path to configuration file
            use_env: Whether to use environment variables
            defaults: Default configuration
            
        Returns:
            Merged configuration
        """
        # Start with defaults
        config = defaults or SecurityAssistantConfig()
        
        # Merge with config file
        if config_file:
            file_config = SecurityAssistantConfig.load(config_file)
            config = config.merge(file_config)
        
        # Merge with environment variables
        if use_env:
            env_config = SecurityAssistantConfig.from_env()
            config = config.merge(env_config)
        
        # Validate
        errors = config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        self._config = config
        return config
    
    @property
    def config(self) -> SecurityAssistantConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def create_default_config(self, path: Union[str, Path], format: str = 'yaml') -> None:
        """
        Create a default configuration file.
        
        Args:
            path: Output file path
            format: File format ('yaml' or 'json')
        """
        config = SecurityAssistantConfig()
        config.save(path, format)


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> SecurityAssistantConfig:
    """Get global configuration."""
    return config_manager.config


def load_config(
    config_file: Optional[Union[str, Path]] = None,
    use_env: bool = True
) -> SecurityAssistantConfig:
    """
    Load configuration.
    
    Args:
        config_file: Path to configuration file
        use_env: Whether to use environment variables
        
    Returns:
        Configuration instance
    """
    return config_manager.load_config(config_file, use_env)
