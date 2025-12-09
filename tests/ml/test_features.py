"""
Tests for ML Feature Extraction

Tests feature extraction from UnifiedFinding objects.

Version: 1.0.0
"""


import pytest

from security_assistant.ml.epss import EPSSClient
from security_assistant.ml.features import FeatureExtractor, FeatureVector
from security_assistant.orchestrator import (
    FindingSeverity,
    ScannerType,
    UnifiedFinding,
)


class TestFeatureVector:
    """Test FeatureVector dataclass."""
    
    def test_to_array(self):
        """Test conversion to numpy array."""
        fv = FeatureVector(
            severity_numeric=3.0,
            cvss_score=7.5,
            epss_score=0.85,
            confidence_numeric=2.0,
            has_fix=1.0,
            has_cwe=1.0,
            has_owasp=0.0,
            reference_count=3.0,
            scanner_bandit=1.0,
            scanner_semgrep=0.0,
            scanner_trivy=0.0,
            category_security=1.0,
            category_secret=0.0,
            category_misconfig=0.0,
            category_vulnerability=0.0,
            file_type_python=1.0,
            file_type_javascript=0.0,
            file_type_java=0.0,
            file_type_go=0.0,
            file_type_other=0.0,
        )
        
        arr = fv.to_array()
        
        assert arr.shape == (20,)
        assert arr[0] == 3.0  # severity_numeric
        assert arr[1] == 7.5  # cvss_score
        assert arr[2] == 0.85  # epss_score
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        fv = FeatureVector(
            severity_numeric=3.0,
            cvss_score=7.5,
            epss_score=0.85,
            confidence_numeric=2.0,
            has_fix=1.0,
            has_cwe=1.0,
            has_owasp=0.0,
            reference_count=3.0,
            scanner_bandit=1.0,
            scanner_semgrep=0.0,
            scanner_trivy=0.0,
            category_security=1.0,
            category_secret=0.0,
            category_misconfig=0.0,
            category_vulnerability=0.0,
            file_type_python=1.0,
            file_type_javascript=0.0,
            file_type_java=0.0,
            file_type_go=0.0,
            file_type_other=0.0,
        )
        
        d = fv.to_dict()
        
        assert isinstance(d, dict)
        assert d["severity_numeric"] == 3.0
        assert d["cvss_score"] == 7.5
        assert d["epss_score"] == 0.85
    
    def test_feature_names(self):
        """Test feature names list."""
        names = FeatureVector.feature_names()
        
        assert len(names) == 20
        assert "severity_numeric" in names
        assert "cvss_score" in names
        assert "epss_score" in names


class TestFeatureExtractor:
    """Test FeatureExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create feature extractor without EPSS."""
        return FeatureExtractor(epss_client=None)
    
    @pytest.fixture
    def sample_finding(self):
        """Create sample UnifiedFinding."""
        return UnifiedFinding(
            finding_id="test-001",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="src/app.py",
            line_start=42,
            line_end=42,
            title="SQL Injection",
            description="Potential SQL injection vulnerability",
            code_snippet="cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
            cwe_ids=["CWE-89"],
            owasp_categories=["A03:2021"],
            references=["https://cwe.mitre.org/data/definitions/89.html"],
            fix_available=True,
            fix_guidance="Use parameterized queries",
            confidence="HIGH",
        )
    
    def test_extract_severity(self, extractor, sample_finding):
        """Test severity extraction."""
        features = extractor.extract(sample_finding)
        
        # HIGH = 3.0
        assert features.severity_numeric == 3.0
    
    def test_extract_cvss_fallback(self, extractor, sample_finding):
        """Test CVSS extraction (fallback to severity)."""
        features = extractor.extract(sample_finding)
        
        # HIGH severity -> 7.5 CVSS
        assert features.cvss_score == 7.5
    
    def test_extract_confidence(self, extractor, sample_finding):
        """Test confidence extraction."""
        features = extractor.extract(sample_finding)
        
        # HIGH confidence = 2.0
        assert features.confidence_numeric == 2.0
    
    def test_extract_confidence_default(self, extractor):
        """Test confidence extraction with missing value."""
        finding = UnifiedFinding(
            finding_id="test-002",
            scanner=ScannerType.SEMGREP,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="src/app.js",
            line_start=10,
            line_end=10,
            title="XSS",
            description="Cross-site scripting",
            code_snippet="innerHTML = userInput",
            confidence=None,  # Missing
        )
        
        features = extractor.extract(finding)
        
        # Default to MEDIUM = 1.0
        assert features.confidence_numeric == 1.0
    
    def test_extract_fix_available(self, extractor, sample_finding):
        """Test fix availability extraction."""
        features = extractor.extract(sample_finding)
        
        assert features.has_fix == 1.0
    
    def test_extract_cwe(self, extractor, sample_finding):
        """Test CWE presence extraction."""
        features = extractor.extract(sample_finding)
        
        assert features.has_cwe == 1.0
    
    def test_extract_owasp(self, extractor, sample_finding):
        """Test OWASP presence extraction."""
        features = extractor.extract(sample_finding)
        
        assert features.has_owasp == 1.0
    
    def test_extract_reference_count(self, extractor, sample_finding):
        """Test reference count extraction."""
        features = extractor.extract(sample_finding)
        
        assert features.reference_count == 1.0
    
    def test_extract_scanner_bandit(self, extractor, sample_finding):
        """Test scanner one-hot encoding (Bandit)."""
        features = extractor.extract(sample_finding)
        
        assert features.scanner_bandit == 1.0
        assert features.scanner_semgrep == 0.0
        assert features.scanner_trivy == 0.0
    
    def test_extract_scanner_semgrep(self, extractor):
        """Test scanner one-hot encoding (Semgrep)."""
        finding = UnifiedFinding(
            finding_id="test-003",
            scanner=ScannerType.SEMGREP,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="src/app.js",
            line_start=10,
            line_end=10,
            title="XSS",
            description="Cross-site scripting",
            code_snippet="innerHTML = userInput",
        )
        
        features = extractor.extract(finding)
        
        assert features.scanner_bandit == 0.0
        assert features.scanner_semgrep == 1.0
        assert features.scanner_trivy == 0.0
    
    def test_extract_category_security(self, extractor, sample_finding):
        """Test category one-hot encoding (security)."""
        features = extractor.extract(sample_finding)
        
        assert features.category_security == 1.0
        assert features.category_secret == 0.0
        assert features.category_misconfig == 0.0
        assert features.category_vulnerability == 0.0
    
    def test_extract_category_secret(self, extractor):
        """Test category one-hot encoding (secret)."""
        finding = UnifiedFinding(
            finding_id="test-004",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.CRITICAL,
            category="secret",
            file_path=".env",
            line_start=5,
            line_end=5,
            title="Hardcoded API Key",
            description="API key found in code",
            code_snippet="API_KEY=sk_live_1234567890",
        )
        
        features = extractor.extract(finding)
        
        assert features.category_security == 0.0
        assert features.category_secret == 1.0
        assert features.category_misconfig == 0.0
        assert features.category_vulnerability == 0.0
    
    def test_extract_file_type_python(self, extractor, sample_finding):
        """Test file type extraction (Python)."""
        features = extractor.extract(sample_finding)
        
        assert features.file_type_python == 1.0
        assert features.file_type_javascript == 0.0
        assert features.file_type_java == 0.0
        assert features.file_type_go == 0.0
        assert features.file_type_other == 0.0
    
    def test_extract_file_type_javascript(self, extractor):
        """Test file type extraction (JavaScript)."""
        finding = UnifiedFinding(
            finding_id="test-005",
            scanner=ScannerType.SEMGREP,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="src/app.js",
            line_start=10,
            line_end=10,
            title="XSS",
            description="Cross-site scripting",
            code_snippet="innerHTML = userInput",
        )
        
        features = extractor.extract(finding)
        
        assert features.file_type_python == 0.0
        assert features.file_type_javascript == 1.0
        assert features.file_type_java == 0.0
        assert features.file_type_go == 0.0
        assert features.file_type_other == 0.0
    
    def test_extract_file_type_other(self, extractor):
        """Test file type extraction (other)."""
        finding = UnifiedFinding(
            finding_id="test-006",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.HIGH,
            category="misconfig",
            file_path="Dockerfile",
            line_start=1,
            line_end=1,
            title="Insecure base image",
            description="Using outdated base image",
            code_snippet="FROM ubuntu:18.04",
        )
        
        features = extractor.extract(finding)
        
        assert features.file_type_python == 0.0
        assert features.file_type_javascript == 0.0
        assert features.file_type_java == 0.0
        assert features.file_type_go == 0.0
        assert features.file_type_other == 1.0
    
    def test_extract_batch(self, extractor):
        """Test batch feature extraction."""
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path=f"src/app{i}.py",
                line_start=i,
                line_end=i,
                title=f"Issue {i}",
                description=f"Description {i}",
                code_snippet=f"code {i}",
            )
            for i in range(5)
        ]
        
        feature_vectors = extractor.extract_batch(findings)
        
        assert len(feature_vectors) == 5
        assert all(isinstance(fv, FeatureVector) for fv in feature_vectors)
    
    def test_extract_cve_ids(self, extractor):
        """Test CVE ID extraction."""
        finding = UnifiedFinding(
            finding_id="test-007",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.CRITICAL,
            category="vulnerability",
            file_path="package.json",
            line_start=10,
            line_end=10,
            title="CVE-2024-1234: Critical vulnerability in lodash",
            description="This affects lodash versions < 4.17.21. See CVE-2024-1234 for details.",
            code_snippet='"lodash": "4.17.20"',
            references=[
                "https://nvd.nist.gov/vuln/detail/CVE-2024-1234",
                "https://github.com/advisories/GHSA-xxxx-yyyy-zzzz",
            ],
        )
        
        cve_ids = extractor._extract_cve_ids(finding)
        
        assert "CVE-2024-1234" in cve_ids
        assert len(cve_ids) >= 1


class TestFeatureExtractorWithEPSS:
    """Test FeatureExtractor with EPSS integration."""
    
    @pytest.fixture
    def mock_epss_client(self, mocker):
        """Create mock EPSS client."""
        client = mocker.Mock(spec=EPSSClient)
        client.get_scores.return_value = {"CVE-2024-1234": 0.85}
        return client
    
    @pytest.fixture
    def extractor_with_epss(self, mock_epss_client):
        """Create feature extractor with EPSS."""
        return FeatureExtractor(epss_client=mock_epss_client)
    
    def test_extract_epss_score(self, extractor_with_epss, mock_epss_client):
        """Test EPSS score extraction."""
        finding = UnifiedFinding(
            finding_id="test-008",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.CRITICAL,
            category="vulnerability",
            file_path="package.json",
            line_start=10,
            line_end=10,
            title="CVE-2024-1234: Critical vulnerability",
            description="See CVE-2024-1234",
            code_snippet='"lodash": "4.17.20"',
        )
        
        features = extractor_with_epss.extract(finding)
        
        # Should call EPSS client
        mock_epss_client.get_scores.assert_called_once()
        
        # Should have EPSS score
        assert features.epss_score == 0.85
    
    def test_extract_epss_no_cve(self, extractor_with_epss, mock_epss_client):
        """Test EPSS extraction when no CVE found."""
        finding = UnifiedFinding(
            finding_id="test-009",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="src/app.py",
            line_start=42,
            line_end=42,
            title="SQL Injection",
            description="Potential SQL injection",
            code_snippet="cursor.execute(query)",
        )
        
        features = extractor_with_epss.extract(finding)
        
        # Should not call EPSS client (no CVE)
        mock_epss_client.get_scores.assert_not_called()
        
        # Should have zero EPSS score
        assert features.epss_score == 0.0
