"""
Config command implementation.

Manages configuration:
- Create default config  
- List configuration options
- Validate configuration files
"""

import logging

from security_assistant.ci.base import (
    get_logger,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from security_assistant.config import ConfigManager


def cmd_config(args):
    """
    Manage configuration.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        manager = ConfigManager()

        if args.create:
            manager.create_default_config()
            path = manager.get_config_path()
            print_success(f"✓ Created default config: {path}")
            
            # Show sample usage
            print("\n📋 Sample configuration:")
            print("security-assistant scan --config config.yaml")
            print("security-assistant report --config config.yaml")
            return 0

        if args.list:
            print_info("📋 Configuration options:")
            
            # Show current config if it exists
            config_path = manager.get_config_path()
            if config_path.exists():
                print(f"Current config: {config_path}")
                try:
                    from security_assistant.config import load_config
                    config = load_config()
                    print(f"  llm_provider: {config.llm.provider}")
                    print(f"  bandit: enabled={config.bandit.enabled}")
                    print(f"  semgrep: enabled={config.semgrep.enabled}")
                    print(f"  trivy: enabled={config.trivy.enabled}")
                except Exception as e:
                    print_warning(f"⚠️ Failed to load current config: {e}")
            else:
                print_warning("No configuration file found")
                print_info("Create with: security-assistant config --create")
                print_info("Default location: ~/.factory/security-assistant.yaml")
            
            return 0

        if args.validate:
            config_path = manager.get_config_path()
            
            if not config_path.exists():
                print_error(f"Configuration file not found: {config_path}")
                return 1
            
            try:
                from security_assistant.config import load_config
                print_info(f"Validating configuration: {config_path}")
                config = load_config(config_path)
                print_success("✅ Configuration is valid")
                return 0
                
            except Exception as e:
                print_error(f"❌ Configuration validation failed: {e}")
                return 1

        # Default action - show current config status
        config_path = manager.get_config_path()
        if config_path.exists():
            print_info(f"Configuration file: {config_path}")
            try:
                from security_assistant.config import load_config
                config = load_config()
                
                print("\n📋 Configuration status:")
                
                # LLM
                print("  🤖 AI Features:")
                print(f"    provider: {config.llm.provider}")
                if hasattr(config.llm, 'model'):
                    print(f"    model: {config.llm.model}")
                
                # Scanners
                print("  🔬 Scanners:")
                print(f"    bandit: {'✓' if config.bandit.enabled else '✗'}")
                print(f"    semgrep: {'✓' if config.semgrep.enabled else '✗'}")
                print(f"    trivy: {'✓' if config.trivy.enabled else '✗'}")
                print(f"    nuclei: {'✓' if config.nuclei.enabled else '✗'}")
                
                # Settings
                print("  ⚙️  Settings:")
                print(f"    output_dir: {config.report.output_dir}")
                print(f"    log_level: {logging.getLogger().level}")
                
            except Exception as e:
                print_warning(f"⚠️ Could not load configuration: {e}")
        else:
            print_warning("No configuration file found")
            print_info("Create with: security-assistant config --create")
            print_info("Default location: ~/.factory/security-assistant.yaml")
        
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Config command failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
