"""
EPUB3 parser — preserves MathML, extracts spine order.
"""
from __future__ import annotations

import os
from pathlib import Path

from ebooklib import epub

from .base import BaseParser, ParsedBook


class EPUB3Parser(BaseParser):
    """Parse EPUB3 files while preserving MathML and structural integrity."""

    def parse(self, path: str) -> ParsedBook:
        book = epub.read_epub(path)
        result = ParsedBook()

        # Metadata
        result.title = self._get_meta(book, "title") or Path(path).stem
        result.language = self._get_meta(book, "language") or "en"
        result.authors = [a[0] for a in book.get_metadata("DC", "creator")]

        # Spine chapters (in reading order)
        for idref, _ in book.spine:
            item = book.get_item_with_id(idref)
            if item and isinstance(item, epub.EpubHtml):
                content = item.get_content()
                html = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
                result.chapters.append({
                    "id": item.get_id(),
                    "name": item.get_name(),
                    "content": content,
                    "html": html,
                    "size": len(content),
                })
                if "math xmlns" in html or "<math" in html:
                    result.has_mathml = True

        # Assets
        for item in book.get_items_of_type(epub.EpubItem.ITEM_IMAGE):
            result.images[item.get_name()] = item.get_content()

        for item in book.get_items_of_type(epub.EpubItem.ITEM_STYLE):
            result.styles.append(item.get_content())

        for item in book.get_items_of_type(epub.EpubItem.ITEM_FONT):
            result.fonts.append(item.get_content())

        result.total_bytes = os.path.getsize(path)
        result.metadata["original_size_mb"] = result.total_bytes / (1024 * 1024)
        result.metadata["chapter_count"] = len(result.chapters)
        result.metadata["image_count"] = len(result.images)
        result.metadata["font_count"] = len(result.fonts)

        return result

    def _get_meta(self, book: epub.EpubBook, name: str) -> str | None:
        meta = book.get_metadata("DC", name)
        return meta[0][0] if meta else None
