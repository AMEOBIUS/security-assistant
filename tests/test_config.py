"""
Tests for security_assistant.config module
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from security_assistant.config import (
    SecurityAssistantConfig,
    BanditConfig,
    SemgrepConfig,
    TrivyConfig,
    OrchestratorConfig,
    ReportConfig,
    GitLabConfig,
    ThresholdConfig,
    ConfigManager,
    DeduplicationStrategy,
    ReportFormat,
    get_config,
    load_config
)


class TestScannerConfigs:
    """Tests for scanner configuration classes"""
    
    def test_bandit_config_defaults(self):
        """Test BanditConfig default values"""
        config = BanditConfig()
        
        assert config.enabled is True
        assert config.severity_level == "low"
        assert config.confidence_level == "low"
        assert "tests" in config.exclude_dirs
        assert config.timeout == 300
    
    def test_semgrep_config_defaults(self):
        """Test SemgrepConfig default values"""
        config = SemgrepConfig()
        
        assert config.enabled is True
        assert config.rules == ["auto"]
        assert config.max_memory == 5000
        assert config.timeout == 300
    
    def test_trivy_config_defaults(self):
        """Test TrivyConfig default values"""
        config = TrivyConfig()
        
        assert config.enabled is True
        assert "CRITICAL" in config.severity
        assert "vuln" in config.scanners
        assert ".git" in config.skip_dirs


class TestMainConfig:
    """Tests for SecurityAssistantConfig"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = SecurityAssistantConfig()
        
        assert isinstance(config.bandit, BanditConfig)
        assert isinstance(config.semgrep, SemgrepConfig)
        assert isinstance(config.trivy, TrivyConfig)
        assert config.scan_target == "."
        assert config.verbose is False
        assert config.log_level == "INFO"
    
    def test_config_to_dict(self):
        """Test converting config to dictionary"""
        config = SecurityAssistantConfig()
        data = config.to_dict()
        
        assert 'bandit' in data
        assert 'semgrep' in data
        assert 'trivy' in data
        assert 'orchestrator' in data
        assert 'report' in data
        assert 'gitlab' in data
        assert 'thresholds' in data
    
    def test_config_from_dict(self):
        """Test creating config from dictionary"""
        data = {
            'bandit': {'enabled': False},
            'scan_target': 'src/',
            'verbose': True
        }
        
        config = SecurityAssistantConfig.from_dict(data)
        
        assert config.bandit.enabled is False
        assert config.scan_target == 'src/'
        assert config.verbose is True
    
    def test_config_save_json(self):
        """Test saving config to JSON"""
        config = SecurityAssistantConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save(temp_path, format='json')
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert 'bandit' in data
            assert 'semgrep' in data
        finally:
            os.unlink(temp_path)
    
    def test_config_save_yaml(self):
        """Test saving config to YAML"""
        config = SecurityAssistantConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save(temp_path, format='yaml')
            assert os.path.exists(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_config_save_invalid_format(self):
        """Test saving config with invalid format"""
        config = SecurityAssistantConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported format"):
                config.save(temp_path, format='txt')
        finally:
            os.unlink(temp_path)
    
    def test_config_load_json(self):
        """Test loading config from JSON"""
        data = {
            'bandit': {'enabled': False},
            'scan_target': 'src/'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            config = SecurityAssistantConfig.load(temp_path)
            
            assert config.bandit.enabled is False
            assert config.scan_target == 'src/'
        finally:
            os.unlink(temp_path)
    
    def test_config_load_nonexistent(self):
        """Test loading nonexistent config file"""
        with pytest.raises(FileNotFoundError):
            SecurityAssistantConfig.load('nonexistent.json')
    
    def test_config_load_invalid_format(self):
        """Test loading config with invalid format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                SecurityAssistantConfig.load(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_config_from_env(self):
        """Test creating config from environment variables"""
        env_vars = {
            'SA_BANDIT_ENABLED': 'false',
            'SA_SEMGREP_ENABLED': 'true',
            'SA_MAX_WORKERS': '5',
            'SA_SCAN_TARGET': 'src/',
            'SA_VERBOSE': 'true',
            'SA_LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            config = SecurityAssistantConfig.from_env()
            
            assert config.bandit.enabled is False
            assert config.semgrep.enabled is True
            assert config.orchestrator.max_workers == 5
            assert config.scan_target == 'src/'
            assert config.verbose is True
            assert config.log_level == 'DEBUG'
    
    def test_config_from_env_gitlab(self):
        """Test GitLab config from environment"""
        env_vars = {
            'SA_GITLAB_URL': 'https://gitlab.com',
            'SA_GITLAB_TOKEN': 'test-token',
            'SA_GITLAB_PROJECT_ID': '123'
        }
        
        with patch.dict(os.environ, env_vars):
            config = SecurityAssistantConfig.from_env()
            
            assert config.gitlab.enabled is True
            assert config.gitlab.url == 'https://gitlab.com'
            assert config.gitlab.token == 'test-token'
            assert config.gitlab.project_id == '123'
    
    def test_config_merge(self):
        """Test merging configurations"""
        config1 = SecurityAssistantConfig()
        config1.verbose = False
        
        config2 = SecurityAssistantConfig()
        config2.scan_target = 'src/'
        config2.verbose = True
        config2.log_level = 'DEBUG'
        
        merged = config1.merge(config2)
        
        assert merged.scan_target == 'src/'  # From config2 (override)
        assert merged.verbose is True  # From config2 (override)
        assert merged.log_level == 'DEBUG'  # From config2
    
    def test_config_validate_success(self):
        """Test successful validation"""
        config = SecurityAssistantConfig()
        errors = config.validate()
        
        assert len(errors) == 0
    
    def test_config_validate_no_scanners(self):
        """Test validation with no scanners enabled (Pydantic validates at construction)"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="At least one scanner must be enabled"):
            SecurityAssistantConfig(
                bandit=BanditConfig(enabled=False),
                semgrep=SemgrepConfig(enabled=False),
                trivy=TrivyConfig(enabled=False),
            )
    
    def test_config_validate_invalid_workers(self):
        """Test validation with invalid max_workers (Pydantic validates at construction)"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SecurityAssistantConfig(
                orchestrator=OrchestratorConfig(max_workers=0)
            )
    
    def test_config_validate_gitlab_missing_url(self):
        """Test validation with GitLab enabled but no URL (Pydantic validates at construction)"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="GitLab URL is required"):
            SecurityAssistantConfig(
                gitlab=GitLabConfig(enabled=True, url=None)
            )
    
    def test_config_validate_invalid_log_level(self):
        """Test validation with invalid log level (Pydantic validates at construction)"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SecurityAssistantConfig(log_level='INVALID')


class TestConfigManager:
    """Tests for ConfigManager"""
    
    def test_config_manager_init(self):
        """Test ConfigManager initialization"""
        manager = ConfigManager()
        
        assert manager._config is None
    
    def test_config_manager_load_defaults(self):
        """Test loading default configuration"""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert isinstance(config, SecurityAssistantConfig)
        assert config.scan_target == "."
    
    def test_config_manager_load_from_file(self):
        """Test loading configuration from file"""
        data = {
            'scan_target': 'src/',
            'verbose': True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            config = manager.load_config(config_file=temp_path, use_env=False)
            
            assert config.scan_target == 'src/'
            assert config.verbose is True
        finally:
            os.unlink(temp_path)
    
    def test_config_manager_property(self):
        """Test config property"""
        manager = ConfigManager()
        
        # First access loads config
        config1 = manager.config
        assert isinstance(config1, SecurityAssistantConfig)
        
        # Second access returns same config
        config2 = manager.config
        assert config1 is config2
    
    def test_config_manager_create_default(self):
        """Test creating default config file"""
        manager = ConfigManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager.create_default_config(temp_path, format='json')
            
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert 'bandit' in data
        finally:
            os.unlink(temp_path)
    
    def test_config_manager_validation_error(self):
        """Test validation error during load (Pydantic raises ValidationError)"""
        from pydantic import ValidationError
        data = {
            'bandit': {'enabled': False},
            'semgrep': {'enabled': False},
            'trivy': {'enabled': False}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            
            with pytest.raises(ValidationError, match="At least one scanner must be enabled"):
                manager.load_config(config_file=temp_path, use_env=False)
        finally:
            os.unlink(temp_path)


class TestGlobalFunctions:
    """Tests for global functions"""
    
    def test_get_config(self):
        """Test get_config function"""
        config = get_config()
        
        assert isinstance(config, SecurityAssistantConfig)
    
    def test_load_config_function(self):
        """Test load_config function"""
        config = load_config(use_env=False)
        
        assert isinstance(config, SecurityAssistantConfig)


class TestEnums:
    """Tests for enum classes"""
    
    def test_deduplication_strategy_enum(self):
        """Test DeduplicationStrategy enum"""
        assert DeduplicationStrategy.LOCATION == "location"
        assert DeduplicationStrategy.CONTENT == "content"
        assert DeduplicationStrategy.BOTH == "both"
    
    def test_report_format_enum(self):
        """Test ReportFormat enum"""
        assert ReportFormat.JSON == "json"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.MARKDOWN == "markdown"
        assert ReportFormat.SARIF == "sarif"
        assert ReportFormat.TEXT == "text"
