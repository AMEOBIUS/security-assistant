"""
Tests for Reachability Analysis
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from security_assistant.analysis.reachability.ast_parser import PythonParser
from security_assistant.analysis.reachability.import_tracker import ImportTracker
from security_assistant.analysis.reachability.reachability_analyzer import (
    ReachabilityAnalyzer,
)


class TestReachability(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def create_file(self, name, content):
        path = self.test_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(path)
        
    def test_ast_parser(self):
        """Test basic AST parsing."""
        content = """
import os
from requests import get
import pandas as pd

def my_func():
    print("Hello")
    get("http://example.com")
    
class MyClass:
    def method(self):
        os.path.join("a", "b")
"""
        file_path = self.create_file("test_parser.py", content)
        
        parser = PythonParser()
        parsed = parser.parse_file(file_path)
        
        self.assertIsNotNone(parsed)
        self.assertIn("os", parsed.imports)
        self.assertIn("requests", parsed.imports)
        self.assertIn("pandas", parsed.imports)
        self.assertIn("my_func", parsed.functions)
        self.assertIn("get", parsed.calls)
        self.assertIn("print", parsed.calls)
        self.assertIn("MyClass", parsed.classes)
        
    def test_import_tracker(self):
        """Test import tracking across files."""
        # File 1: Imports requests
        self.create_file("app.py", "import requests\nrequests.get('url')")
        
        # File 2: Imports numpy
        self.create_file("utils.py", "import numpy as np")
        
        # File 3: No imports
        self.create_file("script.py", "print('hello')")
        
        tracker = ImportTracker()
        tracker.scan_directory(str(self.test_dir))
        
        self.assertTrue(tracker.is_library_used("requests"))
        self.assertTrue(tracker.is_library_used("numpy"))
        self.assertFalse(tracker.is_library_used("pandas"))
        
        # Test locations
        req_locs = tracker.get_usage_locations("requests")
        self.assertEqual(len(req_locs), 1)
        self.assertTrue(req_locs[0].endswith("app.py"))
        
    def test_analyzer_reachable(self):
        """Test analyzer finds reachable dependency."""
        self.create_file("main.py", "import flask\napp = flask.Flask(__name__)")
        
        analyzer = ReachabilityAnalyzer(str(self.test_dir))
        result = analyzer.analyze_dependency("flask")
        
        self.assertTrue(result.is_reachable)
        self.assertEqual(result.confidence, 0.5) # Medium confidence for now
        self.assertIn("imported", result.reason)
        
    def test_analyzer_unreachable(self):
        """Test analyzer correctly identifies unreachable dependency."""
        self.create_file("main.py", "import os\nprint('hello')")
        
        analyzer = ReachabilityAnalyzer(str(self.test_dir))
        result = analyzer.analyze_dependency("django")
        
        self.assertFalse(result.is_reachable)
        self.assertEqual(result.confidence, 0.9)
        self.assertIn("never imported", result.reason)

if __name__ == '__main__':
    unittest.main()
