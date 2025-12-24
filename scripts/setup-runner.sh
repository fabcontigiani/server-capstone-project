#!/bin/bash
# GitHub Actions Self-Hosted Runner Setup Script
# Run this script on your deployment server

set -e

RUNNER_VERSION="2.321.0"
RUNNER_DIR="$HOME/actions-runner"

echo "=========================================="
echo "GitHub Actions Self-Hosted Runner Setup"
echo "=========================================="

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root is not recommended."
    echo "   Consider running as a regular user."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create runner directory
echo "📁 Creating runner directory at $RUNNER_DIR"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download runner
echo "📥 Downloading GitHub Actions Runner v${RUNNER_VERSION}..."
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

# Extract
echo "📦 Extracting runner..."
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Install dependencies
echo "📚 Installing dependencies..."
sudo ./bin/installdependencies.sh

echo ""
echo "=========================================="
echo "Runner downloaded and extracted!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Go to your GitHub repository:"
echo "   Settings → Actions → Runners → New self-hosted runner"
echo ""
echo "2. Copy the token from GitHub and run:"
echo "   cd $RUNNER_DIR"
echo "   ./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN"
echo ""
echo "3. Install and start as a service:"
echo "   sudo ./svc.sh install"
echo "   sudo ./svc.sh start"
echo ""
echo "4. Verify the runner is connected:"
echo "   sudo ./svc.sh status"
echo ""
echo "=========================================="
