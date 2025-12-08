"""
Import Tracker

Tracks usage of imported libraries across the codebase.
Determines if a vulnerable library is actually imported.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Set

from .ast_parser import ParsedFile, PythonParser

logger = logging.getLogger(__name__)


class ImportTracker:
    """Tracks library usage in a project."""

    def __init__(self):
        self.parser = PythonParser()
        self.parsed_files: Dict[str, ParsedFile] = {}
        self.project_imports: Set[str] = set()  # All libraries imported by the project

    def scan_directory(self, directory: str):
        """
        Scan directory and build import map.

        Args:
            directory: Root directory to scan
        """
        directory = Path(directory)
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = str(Path(root) / file)
                    parsed = self.parser.parse_file(file_path)
                    if parsed:
                        self.parsed_files[file_path] = parsed
                        self.project_imports.update(parsed.imports)

    def is_library_used(self, library_name: str) -> bool:
        """
        Check if a library is imported anywhere in the project.

        Args:
            library_name: Name of the library (e.g., "requests")

        Returns:
            True if imported, False otherwise
        """
        # Simple check: is the base module imported?
        # Handles cases like "import requests" or "from requests import get"
        # Logic in ast_parser already extracts base module name

        normalized_name = library_name.lower().replace("-", "_")

        for imp in self.project_imports:
            if imp.lower() == normalized_name:
                return True
        return False

    def get_usage_locations(self, library_name: str) -> List[str]:
        """
        Get list of files that import the library.

        Args:
            library_name: Name of the library

        Returns:
            List of file paths
        """
        locations = []
        normalized_name = library_name.lower().replace("-", "_")

        for path, parsed in self.parsed_files.items():
            for imp in parsed.imports:
                if imp.lower() == normalized_name:
                    locations.append(path)
                    break
        return locations
