#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== ARC-AGI Swarm Setup ==="

# Check Python
python3 --version || { echo "Python 3.12+ required"; exit 1; }

# Create venv if not exists
if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install
pip install -r requirements.txt

# Copy env template
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env — EDIT IT WITH YOUR KEYS (never commit)"
fi

# Verify
echo "=== Verify ==="
python3 -c "from src.nvidia_swarm import NvidiaSwarmDAG; print('Import OK')"

echo "=== Done ==="
echo "Next: edit .env, then run: python -m src.nvidia_swarm.swarm_main"
