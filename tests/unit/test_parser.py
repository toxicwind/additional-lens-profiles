"""Test EPUB3 parser."""
import pytest
from volume.parsers.epub3 import EPUB3Parser


def test_parse_minimal():
    """Test parsing a minimal EPUB structure."""
    # This would need a real EPUB file; placeholder
    parser = EPUB3Parser()
    assert parser is not None


def test_parsed_book_defaults():
    from volume.parsers.base import ParsedBook
    book = ParsedBook()
    assert book.title == ""
    assert book.language == "en"
    assert book.has_mathml is False
