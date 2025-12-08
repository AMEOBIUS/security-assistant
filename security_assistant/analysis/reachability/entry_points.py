"""
Entry Points Detector

Finds entry points in application code.

Entry points are functions that can be called from outside:
- main() functions
- CLI commands
- API endpoints
- Event handlers

Version: 1.0.0
"""

import ast
import logging
from typing import List, Set, Optional
from pathlib import Path

from security_assistant.analysis.reachability.ast_parser import ASTParser


logger = logging.getLogger(__name__)


class EntryPointsDetector:
    """
    Detect entry points in application code.
    
    Entry points are functions that can be invoked from outside
    the application (CLI, API, events, etc).
    
    Example:
        >>> detector = EntryPointsDetector()
        >>> entry_points = detector.find_entry_points("src/")
        >>> print(entry_points)  # ["main", "app.route.index", ...]
    """
    
    # Common entry point patterns
    ENTRY_POINT_PATTERNS = [
        "main",                 # main() function
        "__main__",             # if __name__ == "__main__"
        "cli",                  # CLI commands
        "command",              # CLI commands
        "route",                # Flask/FastAPI routes
        "endpoint",             # API endpoints
        "handler",              # Event handlers
        "on_",                  # Event handlers (on_message, on_click)
        "handle_",              # Event handlers
    ]
    
    # Decorator patterns for entry points
    DECORATOR_PATTERNS = [
        "app.route",            # Flask @app.route
        "router.get",           # FastAPI @router.get
        "router.post",          # FastAPI @router.post
        "click.command",        # Click CLI @click.command
        "command",              # CLI decorators
    ]
    
    def __init__(self):
        """Initialize entry points detector."""
        self.parser = ASTParser()
        logger.info("Initialized EntryPointsDetector")
    
    def find_entry_points(
        self,
        directory: str,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Set[str]:
        """
        Find all entry points in directory.
        
        Args:
            directory: Directory to scan
            exclude_patterns: Patterns to exclude
        
        Returns:
            Set of entry point function names
        
        Example:
            >>> detector = EntryPointsDetector()
            >>> entry_points = detector.find_entry_points("src/")
            >>> print(entry_points)  # {"main", "app.index", ...}
        """
        exclude_patterns = exclude_patterns or []
        
        # Find all Python files
        python_files = list(Path(directory).rglob("*.py"))
        
        entry_points = set()
        
        for file_path in python_files:
            file_str = str(file_path)
            
            # Check exclude patterns
            excluded = False
            for pattern in exclude_patterns:
                if pattern in file_str:
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # Find entry points in file
            file_entry_points = self._find_entry_points_in_file(file_str)
            entry_points.update(file_entry_points)
        
        logger.info(f"Found {len(entry_points)} entry points")
        
        return entry_points
    
    def _find_entry_points_in_file(self, file_path: str) -> Set[str]:
        """
        Find entry points in a single file.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            Set of entry point function names
        """
        tree = self.parser.parse_file(file_path)
        
        if not tree:
            return set()
        
        entry_points = set()
        
        for node in ast.walk(tree):
            # Check function definitions
            if isinstance(node, ast.FunctionDef):
                # Check if function name matches entry point pattern
                if self._is_entry_point_name(node.name):
                    entry_points.add(node.name)
                
                # Check decorators
                for decorator in node.decorator_list:
                    if self._is_entry_point_decorator(decorator):
                        entry_points.add(node.name)
            
            # Check if __name__ == "__main__"
            elif isinstance(node, ast.If):
                if self._is_main_guard(node):
                    # Add "main" as entry point
                    entry_points.add("__main__")
        
        return entry_points
    
    def _is_entry_point_name(self, name: str) -> bool:
        """
        Check if function name indicates entry point.
        
        Args:
            name: Function name
        
        Returns:
            True if entry point, False otherwise
        """
        name_lower = name.lower()
        
        for pattern in self.ENTRY_POINT_PATTERNS:
            if pattern in name_lower:
                return True
        
        return False
    
    def _is_entry_point_decorator(self, decorator: ast.expr) -> bool:
        """
        Check if decorator indicates entry point.
        
        Args:
            decorator: AST decorator node
        
        Returns:
            True if entry point decorator, False otherwise
        """
        # Get decorator name
        decorator_name = self._get_decorator_name(decorator)
        
        if not decorator_name:
            return False
        
        # Check patterns
        for pattern in self.DECORATOR_PATTERNS:
            if pattern in decorator_name:
                return True
        
        return False
    
    def _get_decorator_name(self, decorator: ast.expr) -> Optional[str]:
        """
        Extract decorator name from AST node.
        
        Args:
            decorator: AST decorator node
        
        Returns:
            Decorator name string, or None
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        
        elif isinstance(decorator, ast.Attribute):
            value = self._get_decorator_name(decorator.value)
            if value:
                return f"{value}.{decorator.attr}"
            return decorator.attr
        
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        
        return None
    
    def _is_main_guard(self, node: ast.If) -> bool:
        """
        Check if node is if __name__ == "__main__" guard.
        
        Args:
            node: AST If node
        
        Returns:
            True if main guard, False otherwise
        """
        # Check if condition is comparison
        if not isinstance(node.test, ast.Compare):
            return False
        
        # Check if left side is __name__
        if isinstance(node.test.left, ast.Name):
            if node.test.left.id == "__name__":
                # Check if comparing to "__main__"
                for comparator in node.test.comparators:
                    if isinstance(comparator, ast.Constant):
                        if comparator.value == "__main__":
                            return True
        
        return False
