import pytest

from security_assistant.remediation.advisor import RemediationAdvisor


class TestRemediationAdvisor:
    
    @pytest.fixture
    def advisor(self):
        return RemediationAdvisor()

    def test_analyze_sql_injection(self, advisor):
        vuln_data = {
            "type": "sql_injection",
            "severity": "high"
        }
        advice = advisor.analyze_vulnerability(vuln_data)
        
        assert advice is not None
        assert advice.vulnerability_type == "sql_injection"
        assert advice.severity == "high"
        assert len(advice.remediation_steps) > 0
        
        # Check if we got the template content
        found_remediation = False
        for step in advice.remediation_steps:
            if "parameterized queries" in step.lower():
                found_remediation = True
                break
        
        assert found_remediation or "parameterized queries" in advice.description.lower()
        
        assert advice.code_example is not None
        assert "WHERE username = %s" in advice.code_example

    def test_analyze_mapped_vuln(self, advisor):
        # Test mapping from 'sqli' to 'sql_injection'
        vuln_data = {
            "type": "sqli",
            "severity": "critical"
        }
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert advice.code_example is not None # Should find the SQL injection example

    def test_analyze_xss(self, advisor):
        vuln_data = {"type": "xss", "severity": "medium"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "html.escape" in advice.code_example

    def test_analyze_command_injection(self, advisor):
        vuln_data = {"type": "command_injection", "severity": "high"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "subprocess.run" in advice.code_example

    def test_analyze_path_traversal(self, advisor):
        vuln_data = {"type": "path_traversal", "severity": "high"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "os.path.realpath" in advice.code_example

    def test_analyze_hardcoded_secrets(self, advisor):
        vuln_data = {"type": "hardcoded_secret", "severity": "critical"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "os.environ" in advice.code_example

    def test_analyze_insecure_deserialization(self, advisor):
        vuln_data = {"type": "insecure_deserialization", "severity": "critical"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "json.loads" in advice.code_example

    def test_analyze_csrf(self, advisor):
        vuln_data = {"type": "csrf", "severity": "medium"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "CSRFProtect" in advice.code_example

    def test_analyze_xxe(self, advisor):
        vuln_data = {"type": "xxe", "severity": "high"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "defusedxml" in advice.code_example

    def test_analyze_ssrf(self, advisor):
        vuln_data = {"type": "ssrf", "severity": "high"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "ipaddress" in advice.code_example

    def test_analyze_weak_crypto(self, advisor):
        vuln_data = {"type": "weak_cryptography", "severity": "medium"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "secrets.token_urlsafe" in advice.code_example

    def test_analyze_xss_js(self, advisor):
        vuln_data = {
            "type": "xss",
            "severity": "medium",
            "file_path": "frontend/app.js"
        }
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "textContent" in advice.code_example
        assert "html.escape" not in advice.code_example # Should not contain python code

    def test_analyze_sql_injection_fallback(self, advisor):
        # Test Go example (now available)
        vuln_data = {
            "type": "sql_injection",
            "severity": "high",
            "file_path": "backend/main.go"
        }
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "WHERE username = ?" in advice.code_example # Go example
        assert "db.Query(query, username)" in advice.code_example

    def test_analyze_broken_access_control(self, advisor):
        vuln_data = {"type": "broken_access_control", "severity": "high"}
        advice = advisor.analyze_vulnerability(vuln_data)
        assert advice is not None
        assert "current_user.id != user_id" in advice.code_example

    def test_analyze_unknown_vuln(self, advisor):
        vuln_data = {
            "type": "unknown_bug",
            "severity": "low"
        }
        advice = advisor.analyze_vulnerability(vuln_data)
        
        assert advice is not None
        assert advice.vulnerability_type == "unknown_bug"
        assert advice.code_example is None
        assert len(advice.remediation_steps) == 3 # Default steps


