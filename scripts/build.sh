#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== VOLUME Master Build ==="

# 1. Lint
echo "→ Linting..."
ruff check src/ tests/ agents/ || true
black --check src/ tests/ agents/ || true

# 2. Test
echo "→ Testing..."
pytest tests/ -v

# 3. Build
echo "→ Building..."
python -m build

# 4. Package
echo "→ Packaging..."
mkdir -p dist
cp -r src/ dist/volume-master-src/
cp requirements.txt dist/
cp bootstrap.py dist/
cp README.md dist/

echo "✓ Build complete. Artifacts in dist/"
