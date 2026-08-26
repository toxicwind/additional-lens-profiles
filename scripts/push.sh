#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Verify no secrets in git
echo "=== Secret Check ==="
if git diff --cached --name-only | grep -qE "\.env|auth-profiles|\.key|\.pem"; then
    echo "ERROR: Secrets detected in staged files!"
    exit 1
fi

# Verify .env in .gitignore
if ! grep -q "^\.env" .gitignore; then
    echo "ERROR: .env not in .gitignore!"
    exit 1
fi

echo "→ Adding files..."
git add -A

echo "→ Committing..."
git commit -m "build: volume master $(date -u +%Y-%m-%d-%H%M)"

echo "→ Pushing..."
git push origin main

echo "✓ Pushed. Verify at: https://github.com/toxicwind/additional-lens-profiles"
