"""
EPUB exporter — builds valid EPUB3 with rebuilt nav and TOC.
"""
from __future__ import annotations

import os
from typing import Any

from ebooklib import epub

from ..parsers.base import ParsedBook
from ..splitters.size import VolumePlan


class EPUBExporter:
    """Export a volume plan to a valid EPUB3 file."""

    def export(
        self,
        book: ParsedBook,
        plan: VolumePlan,
        total_volumes: int,
        output_path: str,
        optimize_fonts: bool = False,
        optimize_images: bool = False,
    ) -> dict[str, Any]:
        """Build and write an EPUB volume."""
        new_book = epub.EpubBook()
        new_book.set_title(f"{book.title} - Vol. {plan.volume_index} of {total_volumes} [VOLUME Master]")
        new_book.set_language(book.language)
        new_book.add_author("VOLUME Master Copy System")

        # Add styles
        for i, style_data in enumerate(book.styles):
            item = epub.EpubItem(
                uid=f"style_{i}",
                file_name=f"styles/style_{i}.css",
                media_type="text/css",
                content=style_data,
            )
            new_book.add_item(item)

        # Add fonts
        for i, font_data in enumerate(book.fonts):
            item = epub.EpubItem(
                uid=f"font_{i}",
                file_name=f"fonts/font_{i}.otf",
                media_type="application/vnd.ms-opentype",
                content=font_data,
            )
            new_book.add_item(item)

        # Add needed images
        for img_name in plan.images_needed:
            if img_name in book.images:
                ext = img_name.split(".")[-1].lower()
                media_type = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "gif": "image/gif",
                    "svg": "image/svg+xml",
                    "webp": "image/webp",
                }.get(ext, "image/png")
                item = epub.EpubItem(
                    uid=f"img_{hash(img_name) & 0xFFFFFFFF}",
                    file_name=img_name,
                    media_type=media_type,
                    content=book.images[img_name],
                )
                new_book.add_item(item)

        # Add chapters
        for ch in plan.chapters:
            item = epub.EpubHtml(
                uid=ch["id"],
                file_name=ch["name"],
                content=ch["content"],
            )
            new_book.add_item(item)

        new_book.spine = [ch["id"] for ch in plan.chapters]
        new_book.toc = plan.chapters
        new_book.add_item(epub.EpubNcx())
        new_book.add_item(epub.EpubNav())

        epub.write_epub(output_path, new_book, {})

        return {
            "path": output_path,
            "volume": plan.volume_index,
            "chapters": len(plan.chapters),
            "size_mb": os.path.getsize(output_path) / (1024 * 1024),
        }
