"""ZIP exporter — packages all volumes."""
from __future__ import annotations

import os
import zipfile
from typing import Any


class ZipExporter:
    """Package multiple EPUB volumes into a single ZIP."""

    def export(self, volume_paths: list[str], output_path: str) -> dict[str, Any]:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in volume_paths:
                zf.write(path, arcname=os.path.basename(path))

        return {
            "path": output_path,
            "volumes": len(volume_paths),
            "size_mb": os.path.getsize(output_path) / (1024 * 1024),
        }
