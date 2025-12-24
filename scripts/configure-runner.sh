#!/bin/bash
# Configure and start the GitHub Actions runner
# Usage: ./configure-runner.sh <GITHUB_REPO_URL> <TOKEN>

set -e

RUNNER_DIR="$HOME/actions-runner"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <GITHUB_REPO_URL> <TOKEN>"
    echo "Example: $0 https://github.com/username/repo AXXXXXXXXXX"
    echo ""
    echo "Get your token from:"
    echo "  GitHub Repo → Settings → Actions → Runners → New self-hosted runner"
    exit 1
fi

REPO_URL="$1"
TOKEN="$2"

cd "$RUNNER_DIR"

echo "🔧 Configuring runner for $REPO_URL"
./config.sh --url "$REPO_URL" --token "$TOKEN" --name "$(hostname)" --labels "self-hosted,linux,x64,deploy"

echo ""
echo "📦 Installing runner as a service..."
sudo ./svc.sh install

echo ""
echo "🚀 Starting runner service..."
sudo ./svc.sh start

echo ""
echo "✅ Runner setup complete!"
echo ""
echo "Check status with: sudo $RUNNER_DIR/svc.sh status"
echo "View logs with: journalctl -u actions.runner.* -f"
