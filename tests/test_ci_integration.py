from pathlib import Path

import yaml


class TestCIIntegration:
    def test_dockerfile_exists(self):
        dockerfile = Path("docker/Dockerfile.ci")
        assert dockerfile.exists()
        content = dockerfile.read_text(encoding="utf-8")
        assert "FROM python:3.11-slim" in content
        assert "ENTRYPOINT [\"security-assistant\"]" in content

    def test_gitlab_ci_template_valid(self):
        ci_file = Path("templates/ci/gitlab-ci.yml")
        assert ci_file.exists()
        with open(ci_file) as f:
            data = yaml.safe_load(f)
        
        assert "security-assistant-scan" in data
        assert "script" in data["security-assistant-scan"]
        assert "artifacts" in data["security-assistant-scan"]
        assert "reports" in data["security-assistant-scan"]["artifacts"]
        assert "sast" in data["security-assistant-scan"]["artifacts"]["reports"]

    def test_github_actions_workflow_valid(self):
        gh_file = Path("templates/ci/github-actions.yml")
        assert gh_file.exists()
        with open(gh_file) as f:
            data = yaml.safe_load(f)
            
        assert data["name"] == "Security Assistant Scan"
        assert "jobs" in data
        assert "security-scan" in data["jobs"]
        steps = data["jobs"]["security-scan"]["steps"]
        
        # Check for upload-sarif step
        sarif_step = next((s for s in steps if "upload-sarif" in s.get("uses", "")), None)
        assert sarif_step is not None
