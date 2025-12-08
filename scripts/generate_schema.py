#!/usr/bin/env python3
"""
Generate JSON Schema for Security Assistant configuration.

This script generates a JSON Schema from the Pydantic models in
security_assistant.config and saves it to docs/config-schema.json.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from security_assistant.config import SecurityAssistantConfig

def generate_schema():
    """Generate and save JSON Schema."""
    schema = SecurityAssistantConfig.model_json_schema()
    
    # Add meta information for IDEs
    schema["$id"] = "https://github.com/security-assistant/config-schema.json"
    schema["title"] = "Security Assistant Configuration"
    
    # Output path
    output_path = project_root / "docs" / "config-schema.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
        
    print(f"Generated JSON Schema at: {output_path}")

if __name__ == "__main__":
    generate_schema()
