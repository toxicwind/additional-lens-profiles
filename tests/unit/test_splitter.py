"""Test size splitter."""
import pytest
from volume.parsers.base import ParsedBook
from volume.splitters.size import SizeSplitter


def test_splitter_plan_empty():
    book = ParsedBook()
    splitter = SizeSplitter(max_mb=45)
    plans = splitter.plan(book)
    assert len(plans) == 0


def test_splitter_plan_single():
    book = ParsedBook()
    book.chapters = [{"id": "ch1", "name": "ch1.xhtml", "content": b"hello", "html": "hello", "size": 100}]
    splitter = SizeSplitter(max_mb=45)
    plans = splitter.plan(book)
    assert len(plans) == 1
    assert plans[0].volume_index == 1
