# Security Assistant - One-Click Setup Script (Windows)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "🛡️  Security Assistant Setup" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "[1/7] Checking Python..." -NoNewline
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pyVer = python --version 2>&1
    if ($pyVer -match "3\.1[1-9]") {
        Write-Host " OK ($pyVer)" -ForegroundColor Green
    } else {
        Write-Host " Warning: Recommended Python 3.11+, found $pyVer" -ForegroundColor Yellow
    }
} else {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "Python not found. Please install Python 3.11+ from https://python.org" -ForegroundColor Red
    exit 1
}

# 2. Create Virtual Environment
Write-Host "[2/7] Creating Virtual Environment..." -NoNewline
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host " Created" -ForegroundColor Green
} else {
    Write-Host " Already exists" -ForegroundColor Yellow
}

# 3. Activate Venv
Write-Host "[3/7] Activating Virtual Environment..." -NoNewline
try {
    . .\venv\Scripts\Activate.ps1
    Write-Host " Activated" -ForegroundColor Green
} catch {
    Write-Host " Failed to activate" -ForegroundColor Red
    exit 1
}

# 4. Install Dependencies
Write-Host "[4/7] Installing dependencies (this may take a while)..."
pip install --upgrade pip | Out-Null
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "      Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# 5. Install/Check Scanners
Write-Host "[5/7] Checking Security Scanners..."
# Bandit
if (Get-Command "bandit" -ErrorAction SilentlyContinue) {
    Write-Host "      ✅ Bandit installed" -ForegroundColor Green
} else {
    Write-Host "      Installing Bandit..." -NoNewline
    pip install bandit | Out-Null
    Write-Host " Done" -ForegroundColor Green
}
# Semgrep
if (Get-Command "semgrep" -ErrorAction SilentlyContinue) {
    Write-Host "      ✅ Semgrep installed" -ForegroundColor Green
} else {
    Write-Host "      Installing Semgrep..." -NoNewline
    pip install semgrep | Out-Null
    Write-Host " Done" -ForegroundColor Green
}
# Trivy
if (Get-Command "trivy" -ErrorAction SilentlyContinue) {
    Write-Host "      ✅ Trivy installed" -ForegroundColor Green
} else {
    Write-Host "      ⚠️  Trivy not found. Please install manually: https://aquasecurity.github.io/trivy/" -ForegroundColor Yellow
}

# 6. Configuration
Write-Host "[6/7] Configuration..."
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "      Created .env from example" -ForegroundColor Green
        Write-Host "      PLEASE EDIT .env WITH YOUR SETTINGS!" -ForegroundColor Yellow
    } else {
        Write-Host "      .env.example not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "      .env already exists" -ForegroundColor Green
}

# 7. Verification
Write-Host "[7/7] Verifying installation..."
python -m security_assistant.cli --version
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Setup Complete!" -ForegroundColor Cyan
    Write-Host "Run 'python -m security_assistant.cli scan .' to start scanning."
    Write-Host "Run '.\start.ps1' to start the backend."
} else {
    Write-Host "      Verification failed" -ForegroundColor Red
}
