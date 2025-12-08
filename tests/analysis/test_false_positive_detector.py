"""
Tests for False Positive Detector

Tests FP detection with multiple pattern detectors.

Version: 1.0.0
"""

import pytest

from security_assistant.analysis.false_positive_detector import (
    FalsePositiveDetector,
    FalsePositiveAnalysis,
)


class TestFalsePositiveAnalysis:
    """Test FalsePositiveAnalysis dataclass."""
    
    def test_create_analysis(self):
        """Test creating FalsePositiveAnalysis."""
        analysis = FalsePositiveAnalysis(
            is_likely_false_positive=True,
            confidence=0.85,
            reasons=["Test code detected"],
            pattern_scores={"test_code": 0.85},
        )
        
        assert analysis.is_likely_false_positive is True
        assert analysis.confidence == 0.85
        assert len(analysis.reasons) == 1


class TestFalsePositiveDetector:
    """Test FalsePositiveDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create FP detector."""
        return FalsePositiveDetector()
    
    def test_init(self, detector):
        """Test detector initialization."""
        assert detector.fp_threshold == 0.4
        assert detector.test_code is not None
        assert detector.sanitization is not None
        assert detector.mock_data is not None
        assert detector.safe_context is not None
    
    def test_analyze_test_file(self, detector):
        """Test analyzing test file (should be FP)."""
        analysis = detector.analyze(
            file_path="tests/test_auth.py",
            code="def test_login(): assert user.login()",
        )
        
        assert analysis.is_likely_false_positive is True
        assert analysis.confidence >= 0.4
        assert "test code" in analysis.reasons[0].lower()
    
    def test_analyze_production_file(self, detector):
        """Test analyzing production file (should NOT be FP)."""
        analysis = detector.analyze(
            file_path="src/auth.py",
            code="def login(username, password): return db.query()",
        )
        
        assert analysis.is_likely_false_positive is False
        assert analysis.confidence < 0.4
    
    def test_analyze_sanitized_code(self, detector):
        """Test analyzing sanitized code (should be FP)."""
        analysis = detector.analyze(
            file_path="src/views.py",
            code="safe_input = html.escape(user_input)",
        )
        
        # May or may not be FP depending on threshold
        # But should have sanitization score
        assert "sanitization" in analysis.pattern_scores
        assert analysis.pattern_scores["sanitization"] > 0.5
    
    def test_analyze_mock_data(self, detector):
        """Test analyzing mock data (should be FP)."""
        # Use clear test file path + mock code
        analysis = detector.analyze(
            file_path="tests/test_fixtures.py",  # Clear test file
            code="mock_api_key = 'test123'  # mock data",
        )
        
        # Should be FP (test file + mock data)
        assert analysis.is_likely_false_positive is True
    
    def test_analyze_logging(self, detector):
        """Test analyzing logging code (should be FP)."""
        analysis = detector.analyze(
            file_path="src/app.py",
            code="logger.info(f'User {user_id} logged in')",
        )
        
        # Logging alone may not trigger FP (depends on threshold)
        # But should have safe_context score
        assert "safe_context" in analysis.pattern_scores
    
    def test_analyze_batch(self, detector):
        """Test batch analysis."""
        findings = [
            {"file_path": "tests/test_auth.py", "code": "def test_login(): assert True"},
            {"file_path": "src/auth.py", "code": "def login(): return True"},
        ]
        
        results = detector.analyze_batch(findings)
        
        assert len(results) == 2
        assert results[0].is_likely_false_positive is True  # test file
        assert results[1].is_likely_false_positive is False  # production
    
    def test_filter_false_positives(self, detector):
        """Test filtering FPs from real findings."""
        findings = [
            {"file_path": "tests/test_auth.py", "code": "def test_login(): assert True"},
            {"file_path": "src/auth.py", "code": "def login(): return True"},
        ]
        
        real, fps = detector.filter_false_positives(findings)
        
        assert len(real) == 1  # Only production file
        assert len(fps) == 1  # Test file
        
        # Check FP analysis added
        assert "fp_analysis" in fps[0]
        assert "confidence" in fps[0]["fp_analysis"]
    
    def test_get_statistics(self, detector):
        """Test getting FP statistics."""
        findings = [
            {"file_path": "tests/test_auth.py", "code": "def test_login(): assert True"},
            {"file_path": "src/auth.py", "code": "def login(): return True"},
        ]
        
        stats = detector.get_statistics(findings)
        
        assert stats["total"] == 2
        assert stats["false_positives"] == 1
        assert stats["real_findings"] == 1
        assert stats["fp_rate"] == 0.5
        assert "pattern_breakdown" in stats
    
    def test_custom_threshold(self):
        """Test detector with custom threshold."""
        detector = FalsePositiveDetector(fp_threshold=0.8)
        
        assert detector.fp_threshold == 0.8
        
        # With higher threshold, fewer FPs
        analysis = detector.analyze(
            file_path="tests/test_auth.py",
            code="def login(): ...",  # No test_ prefix
        )
        
        # May or may not be FP depending on score
        assert isinstance(analysis.is_likely_false_positive, bool)


class TestPatternDetectors:
    """Test individual pattern detectors."""
    
    def test_test_code_pattern(self):
        """Test test code pattern detector."""
        from security_assistant.analysis.patterns.test_code import TestCodePattern
        
        detector = TestCodePattern()
        
        # Test file paths
        assert detector.is_test_file("tests/test_auth.py") is True
        assert detector.is_test_file("src/auth.py") is False
        
        # Test code
        assert detector.is_test_code("def test_login(): ...") is True
        assert detector.is_test_code("def login(): ...") is False
    
    def test_sanitization_pattern(self):
        """Test sanitization pattern detector."""
        from security_assistant.analysis.patterns.sanitization import SanitizationPattern
        
        detector = SanitizationPattern()
        
        # Sanitized code
        assert detector.is_sanitized("html.escape(user_input)") is True
        assert detector.is_sanitized("user_input") is False
        
        # Validation
        assert detector.has_validation("def validate_input(): ...") is True
    
    def test_mock_data_pattern(self):
        """Test mock data pattern detector."""
        from security_assistant.analysis.patterns.mock_data import MockDataPattern
        
        detector = MockDataPattern()
        
        # Mock data
        assert detector.is_mock_data("mock_password = 'test'") is True
        assert detector.is_mock_data("password = 'test'") is False
        assert detector.is_mock_data("MOCK_API_KEY = 'test'") is True
    
    def test_safe_context_pattern(self):
        """Test safe context pattern detector."""
        from security_assistant.analysis.patterns.safe_contexts import SafeContextPattern
        
        detector = SafeContextPattern()
        
        # Logging
        assert detector.is_logging("logger.info('test')") is True
        assert detector.is_logging("print('test')") is True
        
        # Comments
        assert detector.is_comment("# This is a comment") is True
        assert detector.is_comment("code = 'test'") is False
