"""
AST Parser for Reachability Analysis

Parses source code into Abstract Syntax Trees to extract imports and function calls.
Currently supports: Python.
"""

import ast
import logging
from typing import Dict, Set, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedFile:
    """Result of parsing a file."""
    path: str
    imports: Set[str]  # Imported module names (e.g., "requests", "os.path")
    functions: Set[str]  # Defined function names
    calls: Set[str]  # Called function names (e.g., "requests.get", "print")
    classes: Set[str] # Defined class names

class PythonParser:
    """AST Parser for Python files."""
    
    def parse_file(self, file_path: str) -> Optional[ParsedFile]:
        """
        Parse a Python file and extract imports, definitions, and calls.
        
        Args:
            file_path: Path to the python file
            
        Returns:
            ParsedFile object or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=file_path)
            
            visitor = CodeVisitor()
            visitor.visit(tree)
            
            return ParsedFile(
                path=file_path,
                imports=visitor.imports,
                functions=visitor.functions,
                calls=visitor.calls,
                classes=visitor.classes
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

class CodeVisitor(ast.NodeVisitor):
    """AST Visitor to extract code information."""
    
    def __init__(self):
        self.imports = set()
        self.functions = set()
        self.calls = set()
        self.classes = set()
        
    def visit_Import(self, node):
        """Handle 'import x' statements."""
        for name in node.names:
            self.imports.add(name.name.split('.')[0]) # Base module name
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Handle 'from x import y' statements."""
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        """Handle function definitions."""
        self.functions.add(node.name)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        """Handle async function definitions."""
        self.functions.add(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """Handle class definitions."""
        self.classes.add(node.name)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Handle function calls."""
        call_name = self._get_call_name(node.func)
        if call_name:
            self.calls.add(call_name)
        self.generic_visit(node)
        
    def _get_call_name(self, node) -> Optional[str]:
        """Extract name from a Call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle obj.method()
            value = self._get_call_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return None
