"""
Mock Data Pattern Detector

Detects mock/fixture/stub data that often triggers false positives.

Common patterns:
- mock_, fixture_, stub_
- MOCK_, FIXTURE_, EXAMPLE_
- Mock(), MagicMock(), patch()
- Hardcoded test data

Version: 1.0.0
"""

import re


class MockDataPattern:
    """
    Detects mock/fixture/stub data patterns.
    
    Mock data often contains intentionally insecure values for testing,
    which should not be flagged as real vulnerabilities.
    
    Example:
        >>> detector = MockDataPattern()
        >>> code = "mock_password = 'test123'"
        >>> is_mock = detector.is_mock_data(code)
        >>> print(is_mock)  # True
    """
    
    # Variable name patterns
    MOCK_VARIABLE_PATTERNS = [
        r"\bmock_",             # mock_user, mock_password
        r"\bfixture_",          # fixture_data
        r"\bstub_",             # stub_response
        r"\bfake_",             # fake_user
        r"\btest_",             # test_data
        r"\bexample_",          # example_config
        r"\bdummy_",            # dummy_value
        r"\bsample_",           # sample_data
        r"_mock\b",             # user_mock
        r"_fixture\b",          # data_fixture
        r"_stub\b",             # response_stub
        r"_fake\b",             # user_fake
        r"_test\b",             # data_test
        r"_example\b",          # config_example
        r"_dummy\b",            # value_dummy
        r"_sample\b",           # data_sample
    ]
    
    # Constant patterns (uppercase)
    MOCK_CONSTANT_PATTERNS = [
        r"\bMOCK_",             # MOCK_API_KEY
        r"\bFIXTURE_",          # FIXTURE_DATA
        r"\bTEST_",             # TEST_PASSWORD
        r"\bEXAMPLE_",          # EXAMPLE_SECRET
        r"\bDUMMY_",            # DUMMY_TOKEN
        r"\bSAMPLE_",           # SAMPLE_KEY
    ]
    
    # Function/class patterns
    MOCK_CODE_PATTERNS = [
        r"Mock\(",              # Mock()
        r"MagicMock\(",         # MagicMock()
        r"@patch\(",            # @patch("module")
        r"@mock\.",             # @mock.patch
        r"@fixture",            # @pytest.fixture
        r"\.mock\(",            # unittest.mock()
        r"create_autospec\(",   # create_autospec()
    ]
    
    # Comment patterns
    MOCK_COMMENT_PATTERNS = [
        r"#.*mock",
        r"#.*fixture",
        r"#.*test data",
        r"#.*example",
        r"#.*dummy",
        r"#.*fake",
        r"#.*stub",
    ]
    
    def __init__(self):
        """Initialize mock data pattern detector."""
        # Compile regex patterns
        self._var_patterns = [re.compile(p, re.IGNORECASE) for p in self.MOCK_VARIABLE_PATTERNS]
        self._const_patterns = [re.compile(p) for p in self.MOCK_CONSTANT_PATTERNS]
        self._code_patterns = [re.compile(p) for p in self.MOCK_CODE_PATTERNS]
        self._comment_patterns = [re.compile(p, re.IGNORECASE) for p in self.MOCK_COMMENT_PATTERNS]
    
    def is_mock_data(self, code: str) -> bool:
        """
        Check if code contains mock data patterns.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code contains mock data, False otherwise
        
        Example:
            >>> detector = MockDataPattern()
            >>> code = "mock_password = 'test123'"
            >>> detector.is_mock_data(code)  # True
        """
        # Check variable patterns
        for pattern in self._var_patterns:
            if pattern.search(code):
                return True
        
        # Check constant patterns
        for pattern in self._const_patterns:
            if pattern.search(code):
                return True
        
        # Check code patterns
        for pattern in self._code_patterns:
            if pattern.search(code):
                return True
        
        # Check comment patterns
        for pattern in self._comment_patterns:
            if pattern.search(code):
                return True
        
        return False
    
    def get_confidence(self, code: str) -> float:
        """
        Get confidence score (0.0-1.0) that this is mock data.
        
        Args:
            code: Code snippet to check
        
        Returns:
            Confidence score (0.0 = not mock, 1.0 = definitely mock)
        
        Example:
            >>> detector = MockDataPattern()
            >>> code = "MOCK_API_KEY = 'test123'  # mock data"
            >>> confidence = detector.get_confidence(code)
            >>> print(confidence)  # 1.0 (high confidence)
        """
        matches = 0
        total_patterns = 4  # var, const, code, comment
        
        # Check each pattern type
        if any(p.search(code) for p in self._var_patterns):
            matches += 1
        
        if any(p.search(code) for p in self._const_patterns):
            matches += 1
        
        if any(p.search(code) for p in self._code_patterns):
            matches += 1
        
        if any(p.search(code) for p in self._comment_patterns):
            matches += 1
        
        return matches / total_patterns
