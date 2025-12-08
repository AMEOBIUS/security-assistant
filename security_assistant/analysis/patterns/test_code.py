"""
Test Code Pattern Detector

Detects test files and test code patterns that often trigger false positives.

Common patterns:
- test_*.py, *_test.py, test*.py
- tests/, spec/, __tests__/
- @pytest.mark, @unittest, describe(), it()
- Mock objects, fixtures, stubs

Version: 1.0.0
"""

import re
from pathlib import Path
from typing import Optional


class TestCodePattern:
    """
    Detects test code patterns.

    Test code often contains intentionally vulnerable patterns for testing
    security features, which should not be flagged as real vulnerabilities.

    Example:
        >>> detector = TestCodePattern()
        >>> is_test = detector.is_test_file("tests/test_auth.py")
        >>> print(is_test)  # True
    """

    # File path patterns
    TEST_PATH_PATTERNS = [
        r"test[s]?/",  # tests/, test/
        r"spec[s]?/",  # specs/, spec/
        r"__tests__/",  # __tests__/
        r"\.test\.",  # .test.
        r"\.spec\.",  # .spec.
        r"_test\.",  # _test.
        r"test_",  # test_
        r"fixture",  # fixtures/, fixture.py
    ]

    # Filename patterns
    TEST_FILE_PATTERNS = [
        r"^test_.*\.py$",  # test_*.py
        r"^.*_test\.py$",  # *_test.py
        r"^test.*\.py$",  # test*.py
        r"^.*\.test\.py$",  # *.test.py
        r"^.*\.spec\.py$",  # *.spec.py
        r"^.*_spec\.py$",  # *_spec.py
        r"^test.*\.js$",  # test*.js
        r"^.*\.test\.js$",  # *.test.js
        r"^.*\.spec\.js$",  # *.spec.js
        r"^fixture[s]?.*\.py$",  # fixtures.py, fixture_*.py
        r"^.*_fixture[s]?.*\.py$",  # *_fixtures.py
    ]

    # Code patterns (decorators, functions)
    TEST_CODE_PATTERNS = [
        r"@pytest\.mark\.",  # @pytest.mark.parametrize
        r"@unittest\.",  # @unittest.skip
        r"@test\(",  # @test()
        r"def test_",  # def test_something():
        r"class Test",  # class TestSomething:
        r"describe\(",  # describe("test")
        r"it\(",  # it("should work")
        r"expect\(",  # expect(result).toBe()
        r"assert ",  # assert x == y
        r"mock\.",  # mock.patch
        r"Mock\(",  # Mock()
        r"MagicMock\(",  # MagicMock()
        r"@patch\(",  # @patch("module")
        r"fixture",  # pytest fixture
        r"setUp\(",  # unittest setUp
        r"tearDown\(",  # unittest tearDown
    ]

    def __init__(self):
        """Initialize test code pattern detector."""
        # Compile regex patterns
        self._path_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.TEST_PATH_PATTERNS
        ]
        self._file_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.TEST_FILE_PATTERNS
        ]
        self._code_patterns = [re.compile(p) for p in self.TEST_CODE_PATTERNS]

    def is_test_file(self, file_path: str) -> bool:
        """
        Check if file path indicates a test file.

        Args:
            file_path: File path to check

        Returns:
            True if file is a test file, False otherwise

        Example:
            >>> detector = TestCodePattern()
            >>> detector.is_test_file("tests/test_auth.py")  # True
            >>> detector.is_test_file("src/auth.py")  # False
        """
        # Normalize path
        file_path = file_path.replace("\\", "/")
        filename = Path(file_path).name

        # Check path patterns
        for pattern in self._path_patterns:
            if pattern.search(file_path):
                return True

        # Check filename patterns
        for pattern in self._file_patterns:
            if pattern.match(filename):
                return True

        return False

    def is_test_code(self, code: str) -> bool:
        """
        Check if code contains test patterns.

        Args:
            code: Code snippet to check

        Returns:
            True if code contains test patterns, False otherwise

        Example:
            >>> detector = TestCodePattern()
            >>> code = "def test_login(): assert user.login()"
            >>> detector.is_test_code(code)  # True
        """
        for pattern in self._code_patterns:
            if pattern.search(code):
                return True

        return False

    def get_confidence(self, file_path: str, code: Optional[str] = None) -> float:
        """
        Get confidence score (0.0-1.0) that this is test code.

        Args:
            file_path: File path
            code: Optional code snippet

        Returns:
            Confidence score (0.0 = not test, 1.0 = definitely test)

        Example:
            >>> detector = TestCodePattern()
            >>> confidence = detector.get_confidence(
            ...     "tests/test_auth.py",
            ...     "def test_login(): assert True"
            ... )
            >>> print(confidence)  # 1.0 (high confidence)
        """
        score = 0.0

        # File path check (0.5 weight)
        if self.is_test_file(file_path):
            score += 0.5

        # Code check (0.5 weight)
        if code and self.is_test_code(code):
            score += 0.5

        return min(score, 1.0)
