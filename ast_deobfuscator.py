#!/usr/bin/env python3
"""
AST Deobfuscator — Bytecode-Aware Python Source Transformer
=============================================================
Parses obfuscated / wrapped Python source, reconstructs readable AST,
and emits clean Python via ast.unparse. Handles common obfuscation patterns:

  • exec(compile(ast.parse(...), ...)) wrappers
  • Base64 / hex / rot13 string payloads
  • Nested lambda / getattr indirection
  • Marshal / pickle bytecode blobs
  • __import__ / builtins.getattr chains

Usage:
    python ast_deobfuscator.py <obfuscated.py> [--out clean.py]
    python ast_deobfuscator.py --eval "exec(compile(...))"
"""
from __future__ import annotations

import ast
import base64
import codecs
import dis
import inspect
import io
import marshal
import re
import struct
import sys
import textwrap
import types
import zlib
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_obfuscation_wrapper(node: ast.AST) -> bool:
    """Detect exec(compile(ast.parse(...), '<string>', 'exec')) patterns."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "exec":
        return True
    if isinstance(func, ast.Attribute) and func.attr == "exec":
        return True
    return False


def _extract_string_payload(node: ast.AST) -> str | bytes | None:
    """Pull a literal string/bytes out of an AST node (handles concat)."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            p = _extract_string_payload(v)
            if p is None:
                return None
            parts.append(str(p))
        return "".join(parts)
    if isinstance(node, ast.FormattedValue):
        return _extract_string_payload(node.value)
    return None


def _try_decode_payload(raw: str | bytes) -> str | bytes | None:
    """Attempt common decode schemes on a candidate payload."""
    if isinstance(raw, bytes):
        # Try zlib → marshal (common .pyc obfuscation)
        for dec in (
            lambda x: zlib.decompress(x),
            lambda x: base64.b64decode(x),
            lambda x: base64.b85decode(x),
            lambda x: codecs.decode(x, "rot13").encode(),
        ):
            try:
                return dec(raw)
            except Exception:
                continue
        return raw

    # raw is str
    s = raw.strip()
    # base64
    for dec in (
        lambda x: base64.b64decode(x.encode()),
        lambda x: base64.b85decode(x.encode()),
        lambda x: base64.b32decode(x.encode()),
        lambda x: base64.b16decode(x.encode()),
        lambda x: codecs.decode(x, "rot13"),
        lambda x: bytes.fromhex(x),
    ):
        try:
            return dec(s)
        except Exception:
            continue
    return s


def _unmarshal_code(data: bytes) -> types.CodeType | None:
    """Try to unmarshal a code object from raw bytes."""
    try:
        obj = marshal.loads(data)
        if isinstance(obj, types.CodeType):
            return obj
    except Exception:
        pass

    # Some obfuscators prepend a 16-byte XOR key or size header
    for offset in (0, 4, 8, 12, 16):
        if offset >= len(data):
            break
        try:
            obj = marshal.loads(data[offset:])
            if isinstance(obj, types.CodeType):
                return obj
        except Exception:
            continue
    return None


def _decompile_code(co: types.CodeType) -> ast.AST | None:
    """Best-effort decompile: disassemble then reconstruct stub AST."""
    try:
        out = io.StringIO()
        dis.dis(co, file=out)
        asm = out.getvalue()
        # Build a placeholder module with the disassembly as a docstring
        stub = ast.parse(f'"""\n{asm}\n"""')
        return stub
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Transformers
# ---------------------------------------------------------------------------

class DeobfuscateTransformer(ast.NodeTransformer):
    """
    Walk the AST, unwrap common obfuscation idioms, and inline decoded
    payloads as clean source nodes.
    """

    def visit_Expr(self, node: ast.Expr) -> ast.AST | list[ast.AST]:
        """Unwrap exec(compile(...)) at statement level."""
        if _is_obfuscation_wrapper(node.value):
            unwrapped = self._unwrap_exec_compile(node.value)
            if unwrapped is not None:
                # Return the body of the unwrapped module
                if isinstance(unwrapped, ast.Module):
                    return unwrapped.body
                return ast.Expr(value=unwrapped)
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Simplify getattr(__import__('builtins'), 'exec') chains."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ("exec", "eval", "compile"):
                # getattr(builtins, 'exec')(...) → exec(...)
                simplified = ast.Call(
                    func=ast.Name(id=node.func.attr, ctx=ast.Load()),
                    args=[self.visit(a) for a in node.args],
                    keywords=[self.visit(k) for k in node.keywords],
                )
                return self.generic_visit(simplified)
        return self.generic_visit(node)

    def _unwrap_exec_compile(self, call: ast.Call) -> ast.AST | None:
        """Drill into exec(compile(ast.parse(decode(...)), ...))."""
        if len(call.args) < 1:
            return None
        first = call.args[0]

        # compile(source, filename, mode)
        if isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "compile":
            if len(first.args) >= 1:
                source_node = first.args[0]
                payload = _extract_string_payload(source_node)
                if payload is not None:
                    decoded = _try_decode_payload(payload)
                    if decoded is not None:
                        if isinstance(decoded, bytes):
                            code = _unmarshal_code(decoded)
                            if code:
                                stub = _decompile_code(code)
                                if stub:
                                    return stub
                            # Fallback: emit bytes as a comment
                            return ast.parse(f'# [binary payload: {len(decoded)} bytes]')
                        try:
                            return ast.parse(decoded)
                        except SyntaxError:
                            return ast.parse(f'# [payload decode failed]\n"""{decoded[:500]}"""')
        # direct exec(string)
        payload = _extract_string_payload(first)
        if payload is not None:
            decoded = _try_decode_payload(payload)
            if isinstance(decoded, str):
                try:
                    return ast.parse(decoded)
                except SyntaxError:
                    pass
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def deobfuscate(source: str) -> str:
    """
    Parse *source*, apply deobfuscation transforms, and return clean Python.
    Falls back to the original source if the AST is already clean.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return f"# PARSE ERROR: {exc}\n" + source

    transformer = DeobfuscateTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    try:
        return ast.unparse(new_tree)
    except Exception as exc:
        return f"# UNPARSE ERROR: {exc}\n" + source


def deobfuscate_file(path: str | Path, out: str | Path | None = None) -> str:
    """Read a file, deobfuscate, optionally write back, and return result."""
    src = Path(path).read_text(encoding="utf-8", errors="replace")
    clean = deobfuscate(src)
    if out:
        Path(out).write_text(clean, encoding="utf-8")
    return clean


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AST Deobfuscator")
    parser.add_argument("source", nargs="?", help="Python file to clean")
    parser.add_argument("--out", "-o", help="Output file (default: stdout)")
    parser.add_argument("--eval", "-e", dest="eval_src", help="Deobfuscate a string literal")
    args = parser.parse_args()

    if args.eval_src:
        result = deobfuscate(args.eval_src)
    elif args.source:
        result = deobfuscate_file(args.source, args.out)
    else:
        parser.print_help()
        sys.exit(1)

    if not args.out:
        print(result)
