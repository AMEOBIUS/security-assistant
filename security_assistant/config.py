"""
Configuration management for Security Assistant (Pydantic v2).

This module provides centralized configuration management with:
- Pydantic v2 validation with type coercion
- YAML/JSON configuration files support
- Environment variables with SA_ prefix
- Default values and nested configuration
- Automatic JSON schema generation
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

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


class ScannerConfig(BaseModel):
    """Base configuration for scanners."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    enabled: bool = True
    config_file: Optional[str] = None
    extra_args: List[str] = Field(default_factory=list)
    timeout: int = Field(default=300, ge=1, le=3600)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (backward compatibility)."""
        return self.model_dump()


class BanditConfig(ScannerConfig):
    """Bandit scanner configuration."""

    severity_level: str = Field(default="low", pattern="^(low|medium|high)$")
    confidence_level: str = Field(default="low", pattern="^(low|medium|high)$")
    exclude_dirs: List[str] = Field(
        default_factory=lambda: [
            "tests",
            "test",
            ".git",
            ".venv",
            "venv",
            "node_modules",
        ]
    )
    skip_tests: List[str] = Field(default_factory=list)


class SemgrepConfig(ScannerConfig):
    """Semgrep scanner configuration."""

    extra_args: List[str] = Field(default_factory=lambda: ["--metrics=off"])
    rules: List[str] = Field(default_factory=lambda: ["auto"])
    exclude_rules: List[str] = Field(default_factory=list)
    max_memory: int = Field(default=5000, ge=100, le=50000)
    max_target_bytes: int = Field(default=1000000, ge=1000)


class TrivyConfig(ScannerConfig):
    """Trivy scanner configuration."""

    severity: List[str] = Field(
        default_factory=lambda: ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    )
    scanners: List[str] = Field(default_factory=lambda: ["vuln", "secret", "config"])
    skip_dirs: List[str] = Field(
        default_factory=lambda: [".git", ".venv", "venv", "node_modules"]
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: List[str]) -> List[str]:
        valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}
        for s in v:
            if s.upper() not in valid:
                raise ValueError(f"Invalid severity: {s}. Must be one of {valid}")
        return [s.upper() for s in v]

    @field_validator("scanners")
    @classmethod
    def validate_scanners(cls, v: List[str]) -> List[str]:
        valid = {"vuln", "secret", "config", "license"}
        for s in v:
            if s.lower() not in valid:
                raise ValueError(f"Invalid scanner: {s}. Must be one of {valid}")
        return [s.lower() for s in v]


class NucleiConfig(ScannerConfig):
    """Nuclei scanner configuration."""
    
    templates: List[str] = Field(default_factory=list)
    severity: List[str] = Field(default_factory=lambda: ["critical", "high", "medium"])
    rate_limit: int = Field(default=150, ge=1)


class OrchestratorConfig(BaseModel):
    """Orchestrator configuration."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    deduplication_strategy: DeduplicationStrategy = DeduplicationStrategy.BOTH
    max_workers: int = Field(default=3, ge=1, le=16)
    parallel_execution: bool = True
    continue_on_error: bool = True


class ReportConfig(BaseModel):
    """Report generation configuration."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    formats: List[ReportFormat] = Field(
        default_factory=lambda: [ReportFormat.JSON, ReportFormat.HTML]
    )
    output_dir: str = Field(default="security-reports", min_length=1)
    include_code_snippets: bool = True
    max_snippet_lines: int = Field(default=10, ge=1, le=100)
    group_by: str = Field(default="severity", pattern="^(severity|scanner|file)$")


class GitLabConfig(BaseModel):
    """GitLab integration configuration."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    enabled: bool = False
    url: Optional[str] = None
    token: Optional[str] = None
    project_id: Optional[str] = None
    create_issues: bool = False
    priority_threshold: int = Field(default=70, ge=0, le=100)
    max_issues: int = Field(default=10, ge=1, le=100)
    issue_labels: List[str] = Field(default_factory=lambda: ["security"])
    assignee_ids: List[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_gitlab_config(self) -> "GitLabConfig":
        if self.enabled and not self.url:
            raise ValueError("GitLab URL is required when GitLab is enabled")
        if self.create_issues:
            if not self.token:
                raise ValueError("GitLab token is required for issue creation")
            if not self.project_id:
                raise ValueError("GitLab project_id is required for issue creation")
        return self


class ThresholdConfig(BaseModel):
    """Severity threshold configuration."""

    model_config = ConfigDict(extra="forbid", validate_default=True)

    fail_on_critical: bool = True
    fail_on_high: bool = False
    fail_on_medium: bool = False
    max_critical: int = Field(default=0, ge=0)
    max_high: int = Field(default=10, ge=0)
    max_medium: int = Field(default=50, ge=0)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    NVIDIA = "nvidia"
    DISABLED = "disabled"


class LLMConfig(BaseModel):
    """LLM integration configuration."""
    
    model_config = ConfigDict(extra="ignore")
    
    provider: LLMProvider = Field(default=LLMProvider.DISABLED)
    api_key: Optional[str] = Field(default=None, description="API key (can also be set via env var)")
    model: str = Field(default="", description="Model name (e.g. gpt-4, claude-3-opus)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1)
    timeout: int = Field(default=60, ge=1)
    
    # Provider-specific settings
    api_base: Optional[str] = Field(default=None, description="Custom API base URL (for Ollama/Azure)")
    retries: int = Field(default=3, ge=0, le=10)


class SecurityAssistantConfig(BaseModel):
    """Main configuration for Security Assistant."""

    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        env_prefix="SA_",
        env_nested_delimiter="__",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    bandit: BanditConfig = Field(default_factory=BanditConfig)
    semgrep: SemgrepConfig = Field(default_factory=SemgrepConfig)
    trivy: TrivyConfig = Field(default_factory=TrivyConfig)
    nuclei: NucleiConfig = Field(default_factory=NucleiConfig)
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)
    gitlab: GitLabConfig = Field(default_factory=GitLabConfig)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)

    scan_target: str = Field(default=".", min_length=1)
    verbose: bool = False
    log_level: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    log_file: Optional[str] = None

    @model_validator(mode="after")
    def validate_at_least_one_scanner(self) -> "SecurityAssistantConfig":
        if not any([
            self.bandit.enabled, 
            self.semgrep.enabled, 
            self.trivy.enabled,
            self.nuclei.enabled
        ]):
            raise ValueError("At least one scanner must be enabled")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def validate(self) -> List[str]:
        """Validate configuration (backward compatibility).

        Note: Pydantic validates automatically on creation.
        This method is kept for backward compatibility.

        Returns:
            Empty list (validation happens at construction time)
        """
        return []

    def save(self, path: Union[str, Path], format: str = "yaml") -> None:
        """Save configuration to file."""
        path = Path(path)
        data = self.model_dump(mode="json")

        with open(path, "w") as f:
            if format == "yaml":
                if yaml is None:
                    raise ImportError(
                        "PyYAML is required for YAML format. Install with: pip install pyyaml"
                    )
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif format == "json":
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecurityAssistantConfig":
        """Create configuration from dictionary."""
        return cls.model_validate(data)

    @classmethod
    def load(
        cls, path: Union[str, Path], validate_security: bool = True
    ) -> "SecurityAssistantConfig":
        """Load configuration from file."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        if validate_security and ConfigurationSandbox is not None:
            sandbox = ConfigurationSandbox(project_root=Path.cwd())
            validation_result = sandbox.validate_config_path(path)

            if not validation_result.is_valid:
                error_msg = "Configuration file validation failed:\n" + "\n".join(
                    f"  - {err}" for err in validation_result.errors
                )
                raise ValueError(error_msg)

            import logging

            logger = logging.getLogger(__name__)
            for warning in validation_result.warnings:
                logger.warning(f"Config validation warning: {warning}")

        with open(path) as f:
            if path.suffix in [".yaml", ".yml"]:
                if yaml is None:
                    raise ImportError(
                        "PyYAML is required for YAML format. Install with: pip install pyyaml"
                    )
                data = yaml.safe_load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")

        return cls.model_validate(data)

    @classmethod
    def from_env(cls) -> "SecurityAssistantConfig":
        """Create configuration from environment variables.

        Environment variables (SA_ prefix):
        - SA_BANDIT_ENABLED, SA_SEMGREP_ENABLED, SA_TRIVY_ENABLED
        - SA_DEDUP_STRATEGY, SA_MAX_WORKERS
        - SA_REPORT_FORMATS, SA_OUTPUT_DIR
        - SA_GITLAB_URL, SA_GITLAB_TOKEN, SA_GITLAB_PROJECT_ID
        - SA_FAIL_ON_CRITICAL, SA_FAIL_ON_HIGH, SA_FAIL_ON_MEDIUM
        - SA_SCAN_TARGET, SA_VERBOSE, SA_LOG_LEVEL
        """
        data: dict[str, Any] = {}

        # Scanner enablement
        if os.getenv("SA_BANDIT_ENABLED"):
            data.setdefault("bandit", {})["enabled"] = (
                os.getenv("SA_BANDIT_ENABLED", "").lower() == "true"
            )
        if os.getenv("SA_SEMGREP_ENABLED"):
            data.setdefault("semgrep", {})["enabled"] = (
                os.getenv("SA_SEMGREP_ENABLED", "").lower() == "true"
            )
        if os.getenv("SA_TRIVY_ENABLED"):
            data.setdefault("trivy", {})["enabled"] = (
                os.getenv("SA_TRIVY_ENABLED", "").lower() == "true"
            )
        if os.getenv("SA_NUCLEI_ENABLED"):
            data.setdefault("nuclei", {})["enabled"] = (
                os.getenv("SA_NUCLEI_ENABLED", "").lower() == "true"
            )

        # Orchestrator
        if os.getenv("SA_DEDUP_STRATEGY"):
            data.setdefault("orchestrator", {})["deduplication_strategy"] = os.getenv(
                "SA_DEDUP_STRATEGY"
            )
        if os.getenv("SA_MAX_WORKERS"):
            data.setdefault("orchestrator", {})["max_workers"] = int(
                os.getenv("SA_MAX_WORKERS", "3")
            )

        # Report
        if os.getenv("SA_REPORT_FORMATS"):
            formats = os.getenv("SA_REPORT_FORMATS", "").split(",")
            data.setdefault("report", {})["formats"] = [f.strip() for f in formats]
        if os.getenv("SA_OUTPUT_DIR"):
            data.setdefault("report", {})["output_dir"] = os.getenv("SA_OUTPUT_DIR")

        # GitLab
        if os.getenv("SA_GITLAB_URL"):
            data.setdefault("gitlab", {})["enabled"] = True
            data["gitlab"]["url"] = os.getenv("SA_GITLAB_URL")
        if os.getenv("SA_GITLAB_TOKEN"):
            data.setdefault("gitlab", {})["token"] = os.getenv("SA_GITLAB_TOKEN")
        if os.getenv("SA_GITLAB_PROJECT_ID"):
            data.setdefault("gitlab", {})["project_id"] = os.getenv(
                "SA_GITLAB_PROJECT_ID"
            )
        if os.getenv("SA_GITLAB_CREATE_ISSUES"):
            data.setdefault("gitlab", {})["create_issues"] = (
                os.getenv("SA_GITLAB_CREATE_ISSUES", "").lower() == "true"
            )
        if os.getenv("SA_PRIORITY_THRESHOLD"):
            data.setdefault("gitlab", {})["priority_threshold"] = int(
                os.getenv("SA_PRIORITY_THRESHOLD", "70")
            )

        # Thresholds
        if os.getenv("SA_FAIL_ON_CRITICAL"):
            data.setdefault("thresholds", {})["fail_on_critical"] = (
                os.getenv("SA_FAIL_ON_CRITICAL", "").lower() == "true"
            )
        if os.getenv("SA_FAIL_ON_HIGH"):
            data.setdefault("thresholds", {})["fail_on_high"] = (
                os.getenv("SA_FAIL_ON_HIGH", "").lower() == "true"
            )
        if os.getenv("SA_FAIL_ON_MEDIUM"):
            data.setdefault("thresholds", {})["fail_on_medium"] = (
                os.getenv("SA_FAIL_ON_MEDIUM", "").lower() == "true"
            )

        # General
        if os.getenv("SA_SCAN_TARGET"):
            data["scan_target"] = os.getenv("SA_SCAN_TARGET")
        if os.getenv("SA_VERBOSE"):
            data["verbose"] = os.getenv("SA_VERBOSE", "").lower() == "true"
        if os.getenv("SA_LOG_LEVEL"):
            data["log_level"] = os.getenv("SA_LOG_LEVEL")
        if os.getenv("SA_LOG_FILE"):
            data["log_file"] = os.getenv("SA_LOG_FILE")

        return cls.model_validate(data) if data else cls()

    def merge(self, other: "SecurityAssistantConfig") -> "SecurityAssistantConfig":
        """Merge with another configuration (other takes precedence)."""
        base_dict = self.model_dump()
        other_dict = other.model_dump()

        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(base_dict, other_dict)
        return self.model_validate(merged)


class ConfigManager:
    """Configuration manager with multiple sources."""

    def __init__(self) -> None:
        self._config: Optional[SecurityAssistantConfig] = None

    def load_config(
        self,
        config_file: Optional[Union[str, Path]] = None,
        use_env: bool = True,
        defaults: Optional[SecurityAssistantConfig] = None,
    ) -> SecurityAssistantConfig:
        """Load configuration from multiple sources.

        Priority (highest to lowest):
        1. Environment variables
        2. Configuration file
        3. Defaults
        """
        config = defaults or SecurityAssistantConfig()

        if config_file:
            file_config = SecurityAssistantConfig.load(config_file)
            config = config.merge(file_config)

        if use_env:
            env_config = SecurityAssistantConfig.from_env()
            config = config.merge(env_config)

        self._config = config
        return config

    @property
    def config(self) -> SecurityAssistantConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def create_default_config(
        self, path: Union[str, Path], format: str = "yaml"
    ) -> None:
        """Create a default configuration file."""
        config = SecurityAssistantConfig()
        config.save(path, format)


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> SecurityAssistantConfig:
    """Get global configuration."""
    return config_manager.config


def load_config(
    config_file: Optional[Union[str, Path]] = None, use_env: bool = True
) -> SecurityAssistantConfig:
    """Load configuration."""
    return config_manager.load_config(config_file, use_env)
