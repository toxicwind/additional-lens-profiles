#!/usr/bin/env python3
"""Tectonic Drift Detection for additional-lens-profiles.

Validates the thing this repo actually is: a collection of lens profiles
under lens-profiles/. Fails on corruption / identity drift; warns on
schema-shape drift.

Replaces the copy-pasted Node/lens-orchestrator workflow that could never
pass here (no package.json, no lib/lens-orchestrator, no src/_11ty/lenses,
and a hardcoded repo name from another project).
"""
import glob
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml is not installed (pip install pyyaml)")

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
PROFILE_GLOBS = ("lens-profiles/**/*.yaml", "lens-profiles/**/*.yml")
REQUIRED_FIELDS = ("name", "agent_type")


def main() -> int:
    files = sorted(
        {
            p
            for pattern in PROFILE_GLOBS
            for p in glob.glob(os.path.join(ROOT, pattern), recursive=True)
        }
    )
    errors: list[str] = []
    warnings: list[str] = []
    seen_names: dict[str, str] = {}
    shapes: dict[str, list[str]] = {}
    checked = 0

    if not files:
        errors.append("no lens profile files found under lens-profiles/")

    for path in files:
        rel = os.path.relpath(path, ROOT)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: unparseable YAML: {exc}")
            continue
        except OSError as exc:
            errors.append(f"{rel}: unreadable: {exc}")
            continue

        if doc is None:
            warnings.append(f"{rel}: empty document (stub profile, no content)")
            continue
        if not isinstance(doc, dict):
            errors.append(
                f"{rel}: top-level YAML is {type(doc).__name__}, expected mapping"
            )
            continue

        if set(doc.keys()) == {"profile"} and isinstance(doc["profile"], dict):
            shape, body = "wrapped", doc["profile"]
        else:
            shape, body = "flat", doc
        shapes.setdefault(shape, []).append(rel)
        checked += 1

        for field in REQUIRED_FIELDS:
            if not body.get(field):
                errors.append(f"{rel}: missing required field '{field}'")

        name = body.get("name")
        if name:
            if name in seen_names:
                errors.append(
                    f"{rel}: duplicate profile name '{name}' "
                    f"(also in {seen_names[name]})"
                )
            else:
                seen_names[name] = rel

        if not body.get("model"):
            warnings.append(f"{rel}: no 'model' field")

    if len(shapes) > 1:
        detail = ", ".join(
            f"{shape} ({len(paths)})" for shape, paths in sorted(shapes.items())
        )
        warnings.append(f"schema-shape drift: profiles use mixed shapes: {detail}")

    print(
        f"profiles checked: {checked}  files: {len(files)}  "
        f"errors: {len(errors)}  warnings: {len(warnings)}"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("drift check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
