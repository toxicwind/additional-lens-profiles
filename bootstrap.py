#!/usr/bin/env python3
"""
VOLUME Master Bootstrap — Self-contained, portable setup.
Handles: nest_asyncio, binary deps, venv creation, pip fallback.
Run: python bootstrap.py
"""
from __future__ import annotations

import os
import sys
import subprocess
import urllib.request
import zipfile
import tarfile
import platform
from pathlib import Path

# ── 1. nest_asyncio (embedded, no pip needed) ──
NEST_ASYNCIO_SRC = """
import asyncio
import functools
import inspect
import sys
from contextlib import contextmanager

class NestedAsyncIO:
    def apply(self):
        loop = asyncio.get_event_loop()
        if hasattr(loop, '_nest_patched'):
            return
        self._patch_loop(loop)
        loop._nest_patched = True

    def _patch_loop(self, loop):
        orig_run = loop.run_until_complete
        @functools.wraps(orig_run)
        def run_until_complete(future):
            if loop.is_running():
                raise RuntimeError('Cannot run until complete on running loop')
            return orig_run(future)
        loop.run_until_complete = run_until_complete

        orig_forever = loop.run_forever
        @functools.wraps(orig_forever)
        def run_forever():
            if loop.is_running():
                return
            orig_forever()
        loop.run_forever = run_forever

# Auto-apply
NestedAsyncIO().apply()
"""

# Write embedded nest_asyncio
nest_path = Path(__file__).parent / "src" / "_vendor" / "nest_asyncio.py"
nest_path.parent.mkdir(parents=True, exist_ok=True)
nest_path.write_text(NEST_ASYNCIO_SRC)
sys.path.insert(0, str(nest_path.parent))
import nest_asyncio
nest_asyncio.apply()
print("[BOOTSTRAP] nest_asyncio applied")

# ── 2. Detect environment ──
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"
ARCH = platform.machine().lower()
VENV_DIR = Path(__file__).parent / ".venv"
BIN_DIR = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin")

def run(cmd, **kwargs):
    """Run shell command, print output."""
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

# ── 3. Create venv if missing ──
if not BIN_DIR.exists():
    print("[BOOTSTRAP] Creating virtual environment...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])

PYTHON = BIN_DIR / ("python.exe" if IS_WINDOWS else "python")
PIP = BIN_DIR / ("pip.exe" if IS_WINDOWS else "pip")

# ── 4. Upgrade pip ──
run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"])

# ── 5. Install core deps ──
CORE_DEPS = [
    "ebooklib>=0.18",
    "fonttools>=4.50",
    "gradio>=5.8",
    "httpx[http2]>=0.27",
    "aiohttp>=3.9",
    "pydantic>=2.7",
    "rich>=13.7",
    "typer>=0.12",
    "python-dotenv>=1.0",
    "duckduckgo-search>=6.0",
    "openai>=1.40",
    "pillow>=10.3",
    "lxml>=5.2",
    "cssselect>=1.2",
    "tinycss2>=1.3",
    "zopfli>=0.2",
    "brotli>=1.1",
    "nest-asyncio>=1.6",
]

print("[BOOTSTRAP] Installing core dependencies...")
run([str(PIP), "install"] + CORE_DEPS)

# ── 6. Install dev deps (optional) ──
if os.getenv("VOLUME_DEV"):
    DEV_DEPS = [
        "pytest>=8.0",
        "pytest-asyncio>=0.23",
        "pytest-cov>=5.0",
        "ruff>=0.5",
        "black>=24.0",
        "mypy>=1.10",
    ]
    print("[BOOTSTRAP] Installing dev dependencies...")
    run([str(PIP), "install"] + DEV_DEPS)

# ── 7. Verify ──
print("\n[BOOTSTRAP] Verification:")
run([str(PYTHON), "-c", "import volume; print(f'VOLUME {volume.__version__} OK')"])
run([str(PYTHON), "-c", "import musepool; print('musepool OK')"])
run([str(PYTHON), "-c", "import nest_asyncio; nest_asyncio.apply(); print('nest_asyncio OK')"])

print("\n[BOOTSTRAP] Done. Activate with:")
if IS_WINDOWS:
    print(f"    {BIN_DIR}\Activate.ps1")
else:
    print(f"    source {BIN_DIR}/activate")
