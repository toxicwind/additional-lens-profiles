#!/usr/bin/env python3
"""
Parquet Converter — Batch-convert any file tree to Apache Parquet
=================================================================
Reads every file under given roots, extracts structured metadata
(lines, tokens, AST nodes, entropy, etc.) and writes Parquet tables
via pyarrow — zero in-memory buffering, streaming writer.

Usage:
    python parquet_converter.py /mnt/agents/temp /mnt/agents/output
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA = pa.schema([
    ("root", pa.string()),
    ("relpath", pa.string()),
    ("abspath", pa.string()),
    ("size_bytes", pa.int64()),
    ("mtime", pa.float64()),
    ("sha256", pa.string()),
    ("lines", pa.int64()),
    ("max_line_len", pa.int64()),
    ("entropy", pa.float64()),
    ("is_text", pa.bool_()),
    ("is_json", pa.bool_()),
    ("is_python", pa.bool_()),
    ("ast_nodes", pa.int64()),
    ("ast_errors", pa.string()),
    ("content_preview", pa.string()),
    ("mime_hint", pa.string()),
    ("token_count_estimate", pa.int64()),
])


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    ent = 0.0
    ln = len(data)
    for count in freq.values():
        p = count / ln
        ent -= p * math.log2(p)
    return ent


def _is_text(data: bytes) -> bool:
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _token_estimate(text: str) -> int:
    # Very rough: split on non-alphanumeric
    return len(re.findall(r"[A-Za-z0-9_]+", text))


def _mime_hint(path: Path) -> str:
    s = path.suffix.lower()
    mapping = {
        ".py": "text/x-python",
        ".json": "application/json",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".sh": "text/x-shellscript",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".har": "application/har+json",
        ".so": "application/x-sharedlib",
        ".xml": "text/xml",
    }
    return mapping.get(s, "application/octet-stream")


def _ast_info(text: str, path: Path) -> tuple[int, str]:
    if not path.suffix.lower().endswith(".py"):
        return 0, ""
    try:
        tree = ast.parse(text)
        return len(list(ast.walk(tree))), ""
    except SyntaxError as exc:
        return 0, str(exc)


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------

def analyse_file(root: Path, abspath: Path) -> dict[str, Any]:
    rel = str(abspath.relative_to(root))
    stat = abspath.stat()
    size = stat.st_size
    mtime = stat.st_mtime

    raw = abspath.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace") if _is_text(raw) else ""
    lines = text.count("\n")
    max_line = max((len(l) for l in text.splitlines()), default=0)
    ent = _entropy(raw)
    is_txt = _is_text(raw)
    is_json = is_txt and (rel.endswith(".json") or text.strip().startswith(("{", "[")))
    is_py = rel.endswith(".py")
    ast_n, ast_err = _ast_info(text, abspath) if is_py else (0, "")
    preview = text[:500].replace("\x00", "")
    mime = _mime_hint(abspath)
    tokens = _token_estimate(text) if is_txt else 0

    return {
        "root": str(root),
        "relpath": rel,
        "abspath": str(abspath),
        "size_bytes": size,
        "mtime": mtime,
        "sha256": sha,
        "lines": lines,
        "max_line_len": max_line,
        "entropy": round(ent, 4),
        "is_text": is_txt,
        "is_json": is_json,
        "is_python": is_py,
        "ast_nodes": ast_n,
        "ast_errors": ast_err,
        "content_preview": preview,
        "mime_hint": mime,
        "token_count_estimate": tokens,
    }


# ---------------------------------------------------------------------------
# Streaming writer
# ---------------------------------------------------------------------------

def convert_tree(writer: pq.ParquetWriter, root: Path) -> int:
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            row = analyse_file(root, path)
        except OSError:
            continue
        batch = pa.RecordBatch.from_pylist([row], schema=SCHEMA)
        writer.write_batch(batch)
        count += 1
    return count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    roots = [Path(p) for p in sys.argv[1:]]
    if not roots:
        print(f"Usage: {sys.argv[0]} <root1> [root2] ...")
        return 1

    out_path = Path("/mnt/agents/output/moonbox-audit/audit_files.parquet")
    writer = pq.ParquetWriter(str(out_path), SCHEMA, compression="zstd")
    total = 0
    for root in roots:
        if not root.exists():
            print(f"[!] Skip missing root: {root}")
            continue
        n = convert_tree(writer, root)
        total += n
        print(f"[+] {root}: {n} files")
    writer.close()
    print(f"[=>] Wrote {total} rows to {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
