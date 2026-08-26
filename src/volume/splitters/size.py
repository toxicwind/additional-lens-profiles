"""
Size-based splitter — chunks chapters to stay under max MB.
Uses musepool for parallel chapter analysis.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ..parsers.base import ParsedBook


@dataclass
class VolumePlan:
    volume_index: int
    chapters: list[dict]
    estimated_size: int = 0
    images_needed: set[str] = field(default_factory=set)


class SizeSplitter:
    """Split a parsed book into volumes under a size limit."""

    def __init__(self, max_mb: int = 45):
        self.max_bytes = max_mb * 1024 * 1024

    def plan(self, book: ParsedBook) -> list[VolumePlan]:
        """Create a split plan without building actual EPUBs."""
        shared_overhead = sum(len(s) for s in book.styles)

        volumes: list[VolumePlan] = []
        current = VolumePlan(volume_index=1, chapters=[])
        current_size = shared_overhead

        for ch in book.chapters:
            ch_size = ch["size"]
            # Find images referenced by this chapter
            html = ch["html"]
            img_names = set()
            for img_name in book.images:
                if os.path.basename(img_name) in html:
                    img_names.add(img_name)
                    ch_size += len(book.images[img_name])

            if current_size + ch_size > self.max_bytes and current.chapters:
                volumes.append(current)
                current = VolumePlan(volume_index=len(volumes) + 1, chapters=[])
                current_size = shared_overhead

            current.chapters.append(ch)
            current.estimated_size += ch_size
            current.images_needed.update(img_names)
            current_size += ch_size

        if current.chapters:
            volumes.append(current)

        return volumes

    @staticmethod
    def split_chapter(chapter: dict, images: dict[str, bytes]) -> dict[str, Any]:
        """Process a single chapter (called by musepool)."""
        html = chapter["html"]
        # Verify MathML preservation
        has_math = "math xmlns" in html or "<math" in html
        return {
            "id": chapter["id"],
            "size": chapter["size"],
            "has_mathml": has_math,
            "image_refs": [os.path.basename(n) for n in images if os.path.basename(n) in html],
        }
