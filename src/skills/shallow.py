"""
Shallow skill — fast content analysis without full parsing.
Extracts TOC, heading hierarchy, MathML presence.
"""
from __future__ import annotations

import re
from typing import Any


def extract_toc(html_content: str) -> list[dict[str, Any]]:
    """Extract table of contents from HTML headings."""
    headings = []
    for match in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html_content, re.DOTALL):
        level = int(match.group(1))
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        headings.append({"level": level, "text": text})
    return headings


def has_mathml(html_content: str) -> bool:
    """Check if content contains MathML."""
    return "math xmlns" in html_content or "<math" in html_content


def estimate_reading_time(html_content: str, wpm: int = 200) -> int:
    """Estimate reading time in minutes."""
    text = re.sub(r"<[^>]+>", "", html_content)
    words = len(text.split())
    return max(1, words // wpm)


def analyze_chapter(chapter_html: str) -> dict[str, Any]:
    """Shallow analysis of a single chapter."""
    return {
        "toc": extract_toc(chapter_html),
        "has_mathml": has_mathml(chapter_html),
        "reading_time_min": estimate_reading_time(chapter_html),
        "heading_count": len(re.findall(r"<h[1-6]", chapter_html)),
        "image_count": len(re.findall(r"<img[^>]*>", chapter_html)),
        "table_count": len(re.findall(r"<table", chapter_html)),
    }
