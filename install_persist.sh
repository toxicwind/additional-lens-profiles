#!/usr/bin/env bash
# Tool Installation Persistence Script
# Run this after container restart to restore all CLI tools
set -euo pipefail

echo "[*] Restoring moonbox audit toolkit..."

# Symlinks (already in /usr/local/bin, but ensure they exist)
ln -sf /usr/bin/batcat /usr/local/bin/bat 2>/dev/null || true
ln -sf /usr/bin/fdfind /usr/local/bin/fd 2>/dev/null || true
ln -sf /usr/bin/rg /usr/local/bin/rg 2>/dev/null || true
ln -sf /usr/bin/fzf /usr/local/bin/fzf 2>/dev/null || true
ln -sf /usr/bin/hyperfine /usr/local/bin/hyperfine 2>/dev/null || true

# eza (GitHub release, may need re-download if /usr/local/bin wiped)
if [ ! -x /usr/local/bin/eza ]; then
    curl -sL "https://github.com/eza-community/eza/releases/latest/download/eza_x86_64-unknown-linux-gnu.tar.gz" | tar xz -C /tmp
    mv /tmp/eza /usr/local/bin/eza && chmod +x /usr/local/bin/eza
fi

# delta (git-delta, may need re-download)
if [ ! -x /usr/local/bin/delta ] || ! /usr/local/bin/delta --version | grep -q "git-delta"; then
    rm -f /usr/local/bin/delta
    curl -sL "https://github.com/dandavison/delta/releases/download/0.18.2/delta-0.18.2-x86_64-unknown-linux-gnu.tar.gz" | tar xz -C /tmp
    mv /tmp/delta-0.18.2-x86_64-unknown-linux-gnu/delta /usr/local/bin/delta
    chmod +x /usr/local/bin/delta
    rm -rf /tmp/delta-0.18.2-x86_64-unknown-linux-gnu
fi

# Verify
echo "[*] Verification:"
for tool in bat fd rg fzf delta hyperfine eza; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "  [OK] $tool"
    else
        echo "  [MISSING] $tool"
    fi
done

echo "[*] Toolkit restore complete."
