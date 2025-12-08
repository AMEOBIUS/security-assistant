# GitLab CI Integration

Integrate Security Assistant into your GitLab CI pipeline.

## Template Usage

If you have the template available in your instance:

```yaml
include:
  - project: 'security-tools/security-assistant'
    file: '/templates/ci/gitlab-ci.yml'
```

## Manual Configuration

Add this to your `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - security

security-scan:
  stage: security
  image: python:3.11-slim
  before_script:
    - apt-get update && apt-get install -y curl git
    - pip install security-assistant semgrep bandit
    - curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
  script:
    - security-assistant scan . --format sarif,html,json --output-dir gl-sast-report
  artifacts:
    reports:
      sast: gl-sast-report/report.sarif
    paths:
      - gl-sast-report/
    expire_in: 1 week
  allow_failure: true
```

## Features

- **Security Dashboard**: SARIF/JSON reports integrate with GitLab Ultimate Security Dashboard.
- **Merge Request Widgets**: Security findings appear in MR widgets.
- **Artifacts**: Full HTML reports available for download.
