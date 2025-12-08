"""
Doctor Command Logic

Checks system health, dependencies, and configuration.
"""

import shutil
import sys
import platform
from typing import Dict, Tuple
import logging

# Force UTF-8 output for Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

def check_tool(name: str, critical: bool = True) -> Tuple[bool, str]:
    """Check if a tool is installed."""
    path = shutil.which(name)
    if path:
        return True, f"✅ {name} found at {path}"
    else:
        msg = f"{'❌' if critical else '⚠️'} {name} not found"
        return False, msg

def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    version = sys.version_info
    min_ver = (3, 11)
    if version >= min_ver:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor} (Required: 3.11+)"

def check_config() -> Tuple[bool, str]:
    """Check configuration file."""
    from pathlib import Path
    if Path(".env").exists():
        return True, "✅ .env file exists"
    elif Path("security-assistant.yaml").exists():
        return True, "✅ security-assistant.yaml exists"
    else:
        return False, "⚠️  No configuration file found (.env or security-assistant.yaml)"

def run_doctor():
    """Run all health checks."""
    print("🏥 Security Assistant Doctor")
    print("============================")
    
    checks = [
        check_python_version(),
        check_tool("git"),
        check_tool("bandit"),
        check_tool("semgrep"),
        check_tool("trivy", critical=False),
        check_config(),
    ]
    
    all_passed = True
    for passed, msg in checks:
        print(msg)
        if not passed and "❌" in msg:
            all_passed = False
            
    print("\nDiagnostics:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Python: {sys.executable}")
    
    if all_passed:
        print("\n✨ System is ready for scanning!")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please install missing requirements.")
        return 1
