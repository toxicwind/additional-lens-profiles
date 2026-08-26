"""
Font optimizer — subsets fonts using fontTools.
"""
from __future__ import annotations

import io
from typing import Any

try:
    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False


class FontOptimizer:
    """Subset fonts to only glyphs used in the text."""

    def __init__(self, flavor: str = "woff2"):
        self.flavor = flavor

    def optimize(self, font_data: bytes, text: str) -> bytes | None:
        """Subset font to only characters present in text."""
        if not FONTTOOLS_AVAILABLE:
            return None

        try:
            font = TTFont(io.BytesIO(font_data))
            options = Options()
            options.flavor = self.flavor
            options.desubroutinize = True

            subsetter = Subsetter(options=options)
            subsetter.populate(text=text)
            subsetter.subset(font)

            out = io.BytesIO()
            font.save(out)
            return out.getvalue()
        except Exception:
            return None

    def extract_text_from_chapters(self, chapters: list[dict]) -> str:
        """Extract all text content from chapters for font subsetting."""
        text = ""
        for ch in chapters:
            html = ch.get("html", "")
            # Strip tags crudely
            import re
            text += re.sub(r"<[^>]+>", "", html)
        return text
