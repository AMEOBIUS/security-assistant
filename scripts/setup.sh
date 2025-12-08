#!/bin/bash
# Security Assistant - One-Click Setup Script (Linux/macOS)

set -e

echo -e "\033[0;36m🛡️  Security Assistant Setup\033[0m"
echo -e "\033[0;36m============================\033[0m"

# 1. Check Python
echo -n "[1/7] Checking Python... "
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version)
    echo -e "\033[0;32mOK ($PY_VER)\033[0m"
else
    echo -e "\033[0;31mFAILED\033[0m"
    echo "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# 2. Create Virtual Environment
echo -n "[2/7] Creating Virtual Environment... "
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "\033[0;32mCreated\033[0m"
else
    echo -e "\033[0;33mAlready exists\033[0m"
fi

# 3. Activate Venv
echo -n "[3/7] Activating Virtual Environment... "
source venv/bin/activate
echo -e "\033[0;32mActivated\033[0m"

# 4. Install Dependencies
echo "[4/7] Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "      \033[0;32mDependencies installed successfully\033[0m"
else
    echo -e "      \033[0;31mFailed to install dependencies\033[0m"
    exit 1
fi

# 5. Install/Check Scanners
echo "[5/7] Checking Security Scanners..."
# Bandit
if command -v bandit &> /dev/null; then
    echo -e "      \033[0;32m✅ Bandit installed\033[0m"
else
    echo -n "      Installing Bandit... "
    pip install bandit > /dev/null
    echo -e "\033[0;32mDone\033[0m"
fi
# Semgrep
if command -v semgrep &> /dev/null; then
    echo -e "      \033[0;32m✅ Semgrep installed\033[0m"
else
    echo -n "      Installing Semgrep... "
    pip install semgrep > /dev/null
    echo -e "\033[0;32mDone\033[0m"
fi
# Trivy
if command -v trivy &> /dev/null; then
    echo -e "      \033[0;32m✅ Trivy installed\033[0m"
else
    echo -e "      \033[0;33m⚠️  Trivy not found. Install: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh\033[0m"
fi

# 6. Configuration
echo "[6/7] Configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "      \033[0;32mCreated .env from example\033[0m"
        echo -e "      \033[0;33mPLEASE EDIT .env WITH YOUR SETTINGS!\033[0m"
    else
        echo -e "      \033[0;33m.env.example not found\033[0m"
    fi
else
    echo -e "      \033[0;32m.env already exists\033[0m"
fi

# 7. Verification
echo "[7/7] Verifying installation..."
python3 -m security_assistant.cli --version
if [ $? -eq 0 ]; then
    echo ""
    echo -e "\033[0;36m🎉 Setup Complete!\033[0m"
    echo "Run 'python3 -m security_assistant.cli scan .' to start scanning."
else
    echo -e "      \033[0;31mVerification failed\033[0m"
fi
